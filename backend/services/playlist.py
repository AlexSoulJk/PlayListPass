from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from urllib.parse import urlparse
import uuid

from database.models.models import Group, Playlist, User
from database.repos.playlist_repos import PlaylistRepos
from schemas.playlist import (
    PlaylistCreateRequest,
    PlaylistDeleteResponse,
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


class PlayListManager:
    def __init__(self, playlist_repository: PlaylistRepos) -> None:
        self.playlist_repository = playlist_repository

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

    async def remove_song_from_playlist(self, playlist_id, song_id):
        _ = playlist_id
        _ = song_id

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
