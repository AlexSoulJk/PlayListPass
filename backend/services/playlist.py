from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from urllib.parse import urlparse
from dataclasses import dataclass
from datetime import datetime
import re
import uuid

from core.yandex_service.databaseloder.dto import TrackUpsertDTO, YandexTrackUpsertDTO
from database.models.base import StreamingService
from database.models.models import Group, Playlist, Track, User
from database.repos.artist_repos import ArtistRepos
from database.repos.playlist_repos import PlaylistRepos
from database.repos.track_artist_repos import TrackArtistRepos
from database.repos.track_repos import TrackRepos
from database.repos.track_service_link_repos import TrackServiceLinkRepos
from database.repos.yandex_track_repos import YandexTrackRepos
from schemas.playlist import (
    PlaylistCreateRequest,
    PlaylistDeleteResponse,
    PlaylistPlaybackQueueResponse,
    PlaylistPlaybackTrackResponse,
    PlaylistTrackAddRequest,
    PlaylistTrackAddResponse,
    PlaylistTrackDeleteResponse,
    PlaylistTrackItemResponse,
    PlaylistTracksResponse,
    PlaylistImageCommitRequest,
    PlaylistImageDeleteResponse,
    PlaylistImageUploadInitRequest,
    PlaylistImageUploadInitResponse,
    PlaylistItemResponse,
    PlaylistUpdateRequest,
)
from services.storage.base import InvalidStorageFormatError, StorageServiceBase
from services.storage.types import StorageEntity, StorageFileFormat, StorageObjectDescriptor


CONTENT_TYPE_TO_IMAGE_FORMAT: dict[str, StorageFileFormat] = {
    "image/jpg": StorageFileFormat.JPG,
    "image/jpeg": StorageFileFormat.JPEG,
    "image/pjpeg": StorageFileFormat.JPEG,
    "image/png": StorageFileFormat.PNG,
    "image/x-png": StorageFileFormat.PNG,
    "image/webp": StorageFileFormat.WEBP,
}


@dataclass(slots=True)
class _PlaylistTrackServiceMapping:
    service: StreamingService
    service_track_id: str
    external_url: str | None
    cover_url: str | None
    duration_sec: int | None


class PlayListManager:
    def __init__(self, playlist_repository: PlaylistRepos) -> None:
        self.playlist_repository = playlist_repository
        session = playlist_repository.session
        self.track_repository = TrackRepos(session=session)
        self.track_service_link_repository = TrackServiceLinkRepos(session=session)
        self.yandex_track_repository = YandexTrackRepos(session=session)
        self.artist_repository = ArtistRepos(session=session)
        self.track_artist_repository = TrackArtistRepos(session=session)

    async def create_playlist(
        self,
        *,
        user: User,
        payload: PlaylistCreateRequest,
        group: Group,
    ) -> PlaylistItemResponse:
        _ = user  # Reserved for future permission/business logic.
        normalized_name = payload.name.strip()
        if not normalized_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="PLAYLIST_NAME_REQUIRED",
            )
        normalized_image_url = payload.image_url.strip() if payload.image_url else None
        if normalized_image_url == "":
            normalized_image_url = None

        existing_playlist = await self.playlist_repository.get_playlist_by_group_and_name(
            group_id=group.id,
            playlist_name=normalized_name,
        )
        if existing_playlist is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="PLAYLIST_NAME_ALREADY_EXISTS",
            )

        try:
            playlist = await self.playlist_repository.create_playlist(
                playlist_name=normalized_name,
                group_id=group.id,
                image_url=normalized_image_url,
            )
        except IntegrityError as error:
            await self.playlist_repository.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="PLAYLIST_NAME_ALREADY_EXISTS",
            ) from error

        return PlaylistItemResponse(
            id=playlist.id,
            name=playlist.name,
            image_url=playlist.image_url,
        )

    async def get_playlist_or_404(
        self,
        *,
        playlist_id: uuid.UUID,
        group_id: uuid.UUID | None = None,
    ) -> Playlist:
        playlist = await self.playlist_repository.get_playlist_by_id(playlist_id)
        if playlist is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PLAYLIST_NOT_FOUND",
            )

        if group_id is not None and playlist.group_id != group_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PLAYLIST_NOT_FOUND",
            )

        return playlist

    async def update_playlist(
        self,
        *,
        user: User,
        group: Group,
        playlist: Playlist,
        payload: PlaylistUpdateRequest,
    ) -> PlaylistItemResponse:
        _ = user
        self._ensure_playlist_belongs_to_group(playlist=playlist, group=group)

        next_name = payload.name.strip() if payload.name is not None else None
        if next_name == "":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="PLAYLIST_NAME_REQUIRED",
            )

        if next_name is not None:
            duplicate = await self.playlist_repository.get_playlist_by_group_and_name(
                group_id=group.id,
                playlist_name=next_name,
                exclude_playlist_id=playlist.id,
            )
            if duplicate is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="PLAYLIST_NAME_ALREADY_EXISTS",
                )

        try:
            updated = await self.playlist_repository.update_playlist(
                playlist,
                name=next_name,
            )
        except IntegrityError as error:
            await self.playlist_repository.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="PLAYLIST_NAME_ALREADY_EXISTS",
            ) from error

        return PlaylistItemResponse(
            id=updated.id,
            name=updated.name,
            image_url=updated.image_url,
        )

    async def init_playlist_image_upload(
        self,
        *,
        user: User,
        group: Group,
        playlist: Playlist,
        payload: PlaylistImageUploadInitRequest,
        storage_service: StorageServiceBase,
    ) -> PlaylistImageUploadInitResponse:
        _ = user
        self._ensure_playlist_belongs_to_group(playlist=playlist, group=group)

        file_format = self._resolve_playlist_image_format(
            filename=payload.filename,
            content_type=payload.content_type,
        )
        descriptor = StorageObjectDescriptor(
            entity=StorageEntity.PLAYLIST,
            file_format=file_format,
            entity_id=playlist.id,
            filename=self._strip_filename_extension(payload.filename),
        )

        try:
            object_key = storage_service.build_object_key(descriptor)
        except InvalidStorageFormatError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PLAYLIST_IMAGE_UNSUPPORTED_FORMAT",
            ) from error

        try:
            upload_url = await storage_service.generate_presigned_upload_url(
                object_key=object_key,
                content_type=payload.content_type,
            )
        except Exception as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="STORAGE_BACKEND_NOT_AVAILABLE",
            ) from error

        return PlaylistImageUploadInitResponse(
            object_key=object_key,
            upload_url=upload_url,
            file_url=storage_service.build_public_url(object_key=object_key),
            expires_in_seconds=storage_service.presigned_url_ttl_seconds,
        )

    async def commit_playlist_image_upload(
        self,
        *,
        user: User,
        group: Group,
        playlist: Playlist,
        payload: PlaylistImageCommitRequest,
        storage_service: StorageServiceBase,
    ) -> PlaylistItemResponse:
        _ = user
        self._ensure_playlist_belongs_to_group(playlist=playlist, group=group)

        object_key = payload.object_key.strip().lstrip("/")
        if not self._is_playlist_object_key(playlist_id=playlist.id, object_key=object_key):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PLAYLIST_IMAGE_OBJECT_KEY_INVALID",
            )

        try:
            object_exists = await storage_service.object_exists(object_key=object_key)
        except Exception as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="STORAGE_BACKEND_NOT_AVAILABLE",
            ) from error

        if not object_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PLAYLIST_IMAGE_OBJECT_NOT_FOUND",
            )

        previous_object_key = self._extract_object_key_from_stored_value(
            playlist.image_url,
            bucket_name=storage_service.bucket_name,
        )
        image_url = (
            payload.image_url.strip()
            if payload.image_url and payload.image_url.strip()
            else storage_service.build_public_url(object_key=object_key)
        )
        updated_playlist = await self.playlist_repository.update_playlist_image(
            playlist,
            image_url=image_url,
        )

        if previous_object_key and previous_object_key != object_key:
            try:
                await storage_service.delete_object(object_key=previous_object_key)
            except Exception:
                pass

        return PlaylistItemResponse(
            id=updated_playlist.id,
            name=updated_playlist.name,
            image_url=updated_playlist.image_url,
        )

    async def delete_playlist_image(
        self,
        *,
        user: User,
        group: Group,
        playlist: Playlist,
        storage_service: StorageServiceBase,
    ) -> PlaylistImageDeleteResponse:
        _ = user
        self._ensure_playlist_belongs_to_group(playlist=playlist, group=group)

        object_key = self._extract_object_key_from_stored_value(
            playlist.image_url,
            bucket_name=storage_service.bucket_name,
        )
        if object_key:
            try:
                await storage_service.delete_object(object_key=object_key)
            except Exception:
                pass

        await self.playlist_repository.update_playlist_image(playlist, image_url=None)
        return PlaylistImageDeleteResponse(playlist_id=playlist.id)

    async def delete_playlist(
        self,
        *,
        user: User,
        group: Group,
        playlist: Playlist,
        storage_service: StorageServiceBase,
    ) -> PlaylistDeleteResponse:
        _ = user
        self._ensure_playlist_belongs_to_group(playlist=playlist, group=group)

        object_key = self._extract_object_key_from_stored_value(
            playlist.image_url,
            bucket_name=storage_service.bucket_name,
        )
        if object_key:
            try:
                await storage_service.delete_object(object_key=object_key)
            except Exception:
                # Cleanup is best-effort and should not block playlist deletion.
                pass

        deleted = await self.playlist_repository.delete_playlist(playlist_id=playlist.id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PLAYLIST_NOT_FOUND",
            )
        return PlaylistDeleteResponse(playlist_id=playlist.id)

    async def add_track_to_playlist(
        self,
        *,
        user: User,
        group: Group,
        playlist: Playlist,
        payload: PlaylistTrackAddRequest,
    ) -> PlaylistTrackAddResponse:
        self._ensure_playlist_belongs_to_group(playlist=playlist, group=group)

        try:
            track, created_new_track = await self._resolve_track_for_playlist_add(user=user, payload=payload)
            existing_link = await self.playlist_repository.get_playlist_track_link(
                playlist_id=playlist.id,
                track_id=track.id,
            )
            if existing_link is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="PLAYLIST_TRACK_ALREADY_EXISTS",
                )

            await self.playlist_repository.add_playlist_track_link(
                playlist_id=playlist.id,
                track_id=track.id,
            )
            await self.playlist_repository.session.commit()
            return PlaylistTrackAddResponse(
                playlist_id=playlist.id,
                track_id=track.id,
                created_new_track=created_new_track,
            )
        except HTTPException:
            await self.playlist_repository.session.rollback()
            raise
        except Exception as error:
            await self.playlist_repository.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="PLAYLIST_TRACK_ADD_FAILED",
            ) from error

    async def remove_track_from_playlist(
        self,
        *,
        user: User,
        group: Group,
        playlist: Playlist,
        track_id: int,
    ) -> PlaylistTrackDeleteResponse:
        _ = user
        self._ensure_playlist_belongs_to_group(playlist=playlist, group=group)
        try:
            deleted = await self.playlist_repository.delete_playlist_track_link(
                playlist_id=playlist.id,
                track_id=track_id,
            )
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="PLAYLIST_TRACK_NOT_FOUND",
                )
            await self.playlist_repository.session.commit()
            return PlaylistTrackDeleteResponse(
                playlist_id=playlist.id,
                track_id=track_id,
            )
        except HTTPException:
            await self.playlist_repository.session.rollback()
            raise
        except Exception as error:
            await self.playlist_repository.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="PLAYLIST_TRACK_REMOVE_FAILED",
            ) from error

    async def get_playlist_tracks(
        self,
        *,
        user: User,
        group: Group,
        playlist: Playlist,
        storage_service: StorageServiceBase,
    ) -> PlaylistTracksResponse:
        _ = user
        self._ensure_playlist_belongs_to_group(playlist=playlist, group=group)

        playlist_tracks = await self.playlist_repository.list_playlist_tracks(playlist_id=playlist.id)
        items: list[PlaylistTrackItemResponse] = []
        for playlist_track in playlist_tracks:
            track = playlist_track.track
            if track is None:
                continue
            mapping = self._build_playlist_track_mapping(track=track)
            items.append(
                PlaylistTrackItemResponse(
                    track_id=track.id,
                    title=track.title,
                    artist=self._resolve_artist_label(track=track),
                    service=mapping.service,
                    service_track_id=mapping.service_track_id,
                    cover_url=self._resolve_track_cover_url(
                        track=track,
                        mapping=mapping,
                        storage_service=storage_service,
                    ),
                    external_url=mapping.external_url or track.external_url,
                    duration_sec=mapping.duration_sec if mapping.duration_sec is not None else track.duration,
                )
            )

        return PlaylistTracksResponse(
            playlist_id=playlist.id,
            items=items,
        )

    async def get_playlist_first_playable_track(
        self,
        *,
        user: User,
        group: Group,
        playlist: Playlist,
        storage_service: StorageServiceBase,
    ) -> PlaylistPlaybackTrackResponse:
        playback_queue = await self.get_playlist_playback_queue(
            user=user,
            group=group,
            playlist=playlist,
            storage_service=storage_service,
        )
        return playback_queue.items[0]

    async def get_playlist_playback_queue(
        self,
        *,
        user: User,
        group: Group,
        playlist: Playlist,
        storage_service: StorageServiceBase,
    ) -> PlaylistPlaybackQueueResponse:
        _ = user
        self._ensure_playlist_belongs_to_group(playlist=playlist, group=group)

        playlist_tracks = await self.playlist_repository.list_playlist_tracks(playlist_id=playlist.id)
        items: list[PlaylistPlaybackTrackResponse] = []
        for playlist_track in playlist_tracks:
            track = playlist_track.track
            if track is None:
                continue
            try:
                audio_url = await self._resolve_track_audio_url(track=track, storage_service=storage_service)
            except Exception as error:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="STORAGE_BACKEND_NOT_AVAILABLE",
                ) from error
            if audio_url is None:
                continue

            mapping = self._build_playlist_track_mapping(track=track)
            items.append(
                PlaylistPlaybackTrackResponse(
                    playlist_id=playlist.id,
                    track_id=track.id,
                    title=track.title,
                    artist=self._resolve_artist_label(track=track),
                    service=mapping.service,
                    service_track_id=mapping.service_track_id,
                    cover_url=self._resolve_track_cover_url(
                        track=track,
                        mapping=mapping,
                        storage_service=storage_service,
                    ),
                    external_url=mapping.external_url or track.external_url,
                    duration_sec=mapping.duration_sec if mapping.duration_sec is not None else track.duration,
                    audio_url=audio_url,
                )
            )

        if not items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PLAYLIST_AUDIO_NOT_AVAILABLE",
            )

        return PlaylistPlaybackQueueResponse(
            playlist_id=playlist.id,
            items=items,
        )

    async def _resolve_track_for_playlist_add(
        self,
        *,
        user: User,
        payload: PlaylistTrackAddRequest,
    ) -> tuple[Track, bool]:
        if payload.internal_track_id is not None:
            existing_track = await self.playlist_repository.get_track_by_id(payload.internal_track_id)
            if existing_track is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="TRACK_NOT_FOUND",
                )
            return existing_track, False

        service = payload.service
        service_track_id = payload.service_track_id.strip() if payload.service_track_id else None
        title = payload.title.strip() if payload.title else None
        artist = payload.artist.strip() if payload.artist else None
        external_url = payload.external_url.strip() if payload.external_url else None

        if service is None or not service_track_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="TRACK_SOURCE_REQUIRED",
            )
        if not title or not artist:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="TRACK_METADATA_REQUIRED",
            )

        existing_track = await self._find_track_by_service_key(
            service=service,
            service_track_id=service_track_id,
        )
        if existing_track is not None:
            await self._upsert_service_meta(
                track_id=existing_track.id,
                payload=payload,
                service_track_id=service_track_id,
            )
            return existing_track, False

        matched_track = await self._match_track_by_title_artist(
            title=title,
            artist=artist,
        )
        if matched_track is not None:
            await self._upsert_service_meta(
                track_id=matched_track.id,
                payload=payload,
                service_track_id=service_track_id,
            )
            return matched_track, False

        if not external_url:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="TRACK_EXTERNAL_URL_REQUIRED",
            )

        duration_sec = payload.duration_sec if payload.duration_sec is not None else 0
        track_payload = TrackUpsertDTO(
            added_by_user_id=user.id,
            service=service,
            title=title,
            duration=duration_sec,
            duration_ms=duration_sec * 1000 if duration_sec else None,
            external_url=external_url,
            audio_valid_for_mvp=False,
            cover_storage_key=None,
            audio_storage_key=None,
            release_date=None,
            fetched_at=datetime.utcnow(),
        )
        created_track = await self.track_repository.create_track(track_payload)

        await self._upsert_artist_if_missing(track_id=created_track.id, artist_name=artist)
        await self._upsert_service_meta(
            track_id=created_track.id,
            payload=payload,
            service_track_id=service_track_id,
        )

        return created_track, True

    async def _find_track_by_service_key(
        self,
        *,
        service: StreamingService,
        service_track_id: str,
    ) -> Track | None:
        if service == StreamingService.YANDEX_MUSIC:
            yandex_meta = await self.yandex_track_repository.get_by_yandex_track_id(service_track_id)
            if yandex_meta is not None:
                return await self.playlist_repository.get_track_by_id(yandex_meta.track_id)

        link = await self.track_service_link_repository.get_by_service_track_id(
            service=service,
            service_track_id=service_track_id,
        )
        if link is None:
            return None
        return await self.playlist_repository.get_track_by_id(link.track_id)

    async def _match_track_by_title_artist(self, *, title: str, artist: str) -> Track | None:
        candidates = await self.playlist_repository.list_tracks_for_search(
            query_text=title,
            services=[],
        )
        normalized_title = self._normalize_for_match(title)
        normalized_artist = self._normalize_for_match(artist)

        matches: list[Track] = []
        for candidate in candidates:
            if self._normalize_for_match(candidate.title) != normalized_title:
                continue
            if not candidate.track_artists:
                continue
            artist_names = [
                self._normalize_for_match(link.artist.name)
                for link in candidate.track_artists
                if link.artist is not None and link.artist.name
            ]
            if normalized_artist in artist_names:
                matches.append(candidate)

        if not matches:
            return None

        # Temporary deterministic fallback for ambiguous title+artist matches.
        matches.sort(key=lambda track: track.id)
        return matches[0]

    async def _upsert_service_meta(
        self,
        *,
        track_id: int,
        payload: PlaylistTrackAddRequest,
        service_track_id: str,
    ) -> None:
        if payload.service is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="TRACK_SOURCE_REQUIRED",
            )

        await self.track_service_link_repository.upsert_link(
            track_id=track_id,
            service=payload.service,
            service_track_id=service_track_id,
            external_url=payload.external_url,
            cover_url=payload.cover_url,
            duration_sec=payload.duration_sec,
            imported_from_search=payload.imported_from_search,
            fetched_at=datetime.utcnow(),
        )

        if payload.service == StreamingService.YANDEX_MUSIC:
            yandex_payload = YandexTrackUpsertDTO(
                yandex_track_id=service_track_id,
                provider_fetched_at=datetime.utcnow(),
            )
            await self.yandex_track_repository.upsert_yandex_meta(track_id=track_id, payload=yandex_payload)

    async def _upsert_artist_if_missing(self, *, track_id: int, artist_name: str) -> None:
        normalized = artist_name.strip()
        if not normalized:
            return

        existing_track = await self.playlist_repository.get_track_by_id(track_id)
        if existing_track is not None and existing_track.track_artists:
            return

        artist = await self.artist_repository.create_artist_if_missing(normalized)
        await self.track_artist_repository.upsert_track_artist(
            track_id=track_id,
            artist_id=artist.id,
            artist_order=0,
            role=None,
        )

    @staticmethod
    def _resolve_artist_label(*, track: Track) -> str:
        if not track.track_artists:
            return "Unknown artist"
        sorted_links = sorted(
            track.track_artists,
            key=lambda link: (
                link.artist_order if link.artist_order is not None else 999,
                str(link.artist_id),
            ),
        )
        names = [link.artist.name for link in sorted_links if link.artist is not None and link.artist.name]
        return ", ".join(names) if names else "Unknown artist"

    @staticmethod
    def _build_playlist_track_mapping(*, track: Track) -> _PlaylistTrackServiceMapping:
        preferred_link = next(
            (link for link in track.service_links if link.service == track.service),
            None,
        )
        if preferred_link is not None:
            return _PlaylistTrackServiceMapping(
                service=preferred_link.service,
                service_track_id=preferred_link.service_track_id,
                external_url=preferred_link.external_url,
                cover_url=preferred_link.cover_url,
                duration_sec=preferred_link.duration_sec,
            )

        if track.service_links:
            first_link = track.service_links[0]
            return _PlaylistTrackServiceMapping(
                service=first_link.service,
                service_track_id=first_link.service_track_id,
                external_url=first_link.external_url,
                cover_url=first_link.cover_url,
                duration_sec=first_link.duration_sec,
            )

        if track.yandex_meta is not None and track.yandex_meta.yandex_track_id:
            return _PlaylistTrackServiceMapping(
                service=StreamingService.YANDEX_MUSIC,
                service_track_id=track.yandex_meta.yandex_track_id,
                external_url=track.external_url,
                cover_url=None,
                duration_sec=track.duration,
            )

        return _PlaylistTrackServiceMapping(
            service=track.service,
            service_track_id=str(track.id),
            external_url=track.external_url,
            cover_url=None,
            duration_sec=track.duration,
        )

    @staticmethod
    def _resolve_track_cover_url(
        *,
        track: Track,
        mapping: _PlaylistTrackServiceMapping,
        storage_service: StorageServiceBase,
    ) -> str | None:
        if mapping.cover_url:
            return mapping.cover_url
        if not track.cover_storage_key:
            return None
        cleaned = track.cover_storage_key.strip()
        if cleaned.startswith("http://") or cleaned.startswith("https://"):
            return cleaned
        return storage_service.build_public_url(object_key=cleaned.lstrip("/"))

    @staticmethod
    async def _resolve_track_audio_url(
        *,
        track: Track,
        storage_service: StorageServiceBase,
    ) -> str | None:
        if not track.audio_storage_key:
            return None

        cleaned = track.audio_storage_key.strip()
        if not cleaned:
            return None
        if cleaned.startswith("http://") or cleaned.startswith("https://"):
            return cleaned

        object_key = cleaned.lstrip("/")
        bucket_prefix = f"{storage_service.bucket_name.strip('/')}/"
        if object_key.startswith(bucket_prefix):
            object_key = object_key[len(bucket_prefix):]

        object_exists = await storage_service.object_exists(object_key=object_key)
        if not object_exists:
            return None

        try:
            return await storage_service.generate_presigned_download_url(object_key=object_key)
        except Exception:
            return storage_service.build_public_url(object_key=object_key)

    @staticmethod
    def _normalize_for_match(value: str) -> str:
        lowered = value.lower()
        cleaned = re.sub(r"[^a-z0-9а-яё]+", " ", lowered, flags=re.IGNORECASE)
        return " ".join(cleaned.split())

    async def get_user_playlists(self, user_id):
        _ = user_id

    @staticmethod
    def _ensure_playlist_belongs_to_group(*, playlist: Playlist, group: Group) -> None:
        if playlist.group_id != group.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PLAYLIST_NOT_FOUND",
            )

    @staticmethod
    def _resolve_playlist_image_format(*, filename: str, content_type: str | None) -> StorageFileFormat:
        filename_format = PlayListManager._extract_format_from_filename(filename)
        content_type_format = PlayListManager._extract_format_from_content_type(content_type)

        if (
            filename_format
            and content_type_format
            and PlayListManager._normalize_image_format(filename_format)
            != PlayListManager._normalize_image_format(content_type_format)
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PLAYLIST_IMAGE_FORMAT_MISMATCH",
            )

        selected_format = filename_format or content_type_format
        if selected_format is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PLAYLIST_IMAGE_UNSUPPORTED_FORMAT",
            )
        return selected_format

    @staticmethod
    def _extract_format_from_filename(filename: str) -> StorageFileFormat | None:
        if "." not in filename:
            return None
        extension = filename.rsplit(".", maxsplit=1)[-1].lower()
        try:
            return StorageFileFormat(extension)
        except ValueError:
            return None

    @staticmethod
    def _extract_format_from_content_type(content_type: str | None) -> StorageFileFormat | None:
        if not content_type:
            return None
        normalized = content_type.split(";", maxsplit=1)[0].strip().lower()
        return CONTENT_TYPE_TO_IMAGE_FORMAT.get(normalized)

    @staticmethod
    def _normalize_image_format(image_format: StorageFileFormat) -> StorageFileFormat:
        if image_format == StorageFileFormat.JPG:
            return StorageFileFormat.JPEG
        return image_format

    @staticmethod
    def _strip_filename_extension(filename: str) -> str:
        if "." not in filename:
            return filename
        return filename.rsplit(".", maxsplit=1)[0]

    @staticmethod
    def _is_playlist_object_key(*, playlist_id: uuid.UUID, object_key: str) -> bool:
        expected_prefix = f"{StorageEntity.PLAYLIST.value}/{playlist_id}/"
        return object_key.startswith(expected_prefix)

    @staticmethod
    def _extract_object_key_from_stored_value(
        stored_value: str | None,
        *,
        bucket_name: str,
    ) -> str | None:
        if not stored_value:
            return None

        cleaned = stored_value.strip().lstrip("/")
        if not cleaned:
            return None
        if cleaned.startswith(f"{StorageEntity.PLAYLIST.value}/"):
            return cleaned

        parsed = urlparse(cleaned)
        path = parsed.path.lstrip("/")
        if not path:
            return None

        bucket_prefix = f"{bucket_name.strip('/')}/"
        if path.startswith(bucket_prefix):
            return path[len(bucket_prefix):]

        playlist_path_marker = f"{StorageEntity.PLAYLIST.value}/"
        marker_index = path.find(playlist_path_marker)
        if marker_index >= 0:
            return path[marker_index:]

        return path
