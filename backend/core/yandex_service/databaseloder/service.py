from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.yandex_service.databaseloder.dto import (
    ArtistServiceLinkUpsertDTO,
    DbLoaderSettingsDTO,
    LoadStatsDTO,
    TrackArtistLinkDTO,
    TrackImportBundleDTO,
)
from core.yandex_service.databaseloder.mapper import map_card_to_import_bundle
from core.yandex_service.databaseloder.reader import (
    read_dataset_index,
    read_track_card,
    resolve_local_artifact_path,
)
from core.yandex_service.databaseloder.report import (
    append_error,
    create_stats,
    finalize_stats,
    write_report,
)
from database.models.base import StreamingService
from database.repos.artist_repos import ArtistRepos
from database.repos.artist_service_link_repos import ArtistServiceLinkRepos
from database.repos.track_artist_repos import TrackArtistRepos
from database.repos.track_repos import TrackRepos
from database.repos.yandex_track_repos import YandexTrackRepos
from services.storage.base import StorageServiceBase


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LoaderCleanupResult:
    attempted: int = 0
    deleted: int = 0
    missing: int = 0
    errors: int = 0


class YandexDatasetLoaderService:
    def __init__(
        self,
        *,
        session_maker: async_sessionmaker[AsyncSession],
        storage_service: StorageServiceBase,
    ) -> None:
        self.session_maker = session_maker
        self.storage_service = storage_service

    async def run(self, settings: DbLoaderSettingsDTO) -> LoadStatsDTO:
        index_items = read_dataset_index(settings.dataset_dir)
        stats = create_stats(total_cards=len(index_items))

        async with self.session_maker() as session:
            track_repo = TrackRepos(session)
            yandex_repo = YandexTrackRepos(session)
            artist_repo = ArtistRepos(session)
            artist_link_repo = ArtistServiceLinkRepos(session)
            track_artist_repo = TrackArtistRepos(session)

            for index_item in index_items:
                try:
                    card = read_track_card(settings.dataset_dir, index_item)

                    audio_path = self._resolve_audio_path(
                        dataset_dir=settings.dataset_dir,
                        index_audio_path=index_item.audio_path,
                        card_audio_path=card.local_paths.audio_path,
                    )
                    image_path = resolve_local_artifact_path(
                        dataset_dir=settings.dataset_dir,
                        raw_path=card.local_paths.image_path,
                        fallback_subdir="track_image",
                    )

                    if not self._is_mvp_valid(card.provider_info.valid_for_mvp, audio_path):
                        stats.skipped_invalid += 1
                        append_error(
                            stats=stats,
                            service_track_id=index_item.service_track_id,
                            stage="validation",
                            error_type="MVP_INVALID",
                            message=(
                                "Track is skipped: valid_for_mvp=false "
                                "or resolved audio artifact is missing."
                            ),
                        )
                        continue

                    bundle = map_card_to_import_bundle(
                        index_item=index_item,
                        card=card,
                        resolved_audio_path=audio_path,
                        resolved_image_path=image_path,
                    )
                except (FileNotFoundError, ValidationError, ValueError) as exc:
                    stats.skipped_invalid += 1
                    append_error(
                        stats=stats,
                        service_track_id=index_item.service_track_id,
                        stage="read-map",
                        error_type=type(exc).__name__,
                        message=str(exc),
                    )
                    if settings.fail_on_error:
                        break
                    continue
                except Exception as exc:  # pragma: no cover - defensive path
                    stats.skipped_invalid += 1
                    append_error(
                        stats=stats,
                        service_track_id=index_item.service_track_id,
                        stage="read-map",
                        error_type=type(exc).__name__,
                        message=str(exc),
                        with_traceback=True,
                    )
                    if settings.fail_on_error:
                        break
                    continue

                if settings.dry_run:
                    continue

                try:
                    await self._upload_bundle_files(
                        bundle=bundle,
                        resolved_audio_path=audio_path,
                        resolved_image_path=image_path,
                    )
                    created = await self._upsert_bundle(
                        bundle=bundle,
                        track_repo=track_repo,
                        yandex_repo=yandex_repo,
                        artist_repo=artist_repo,
                        artist_link_repo=artist_link_repo,
                        track_artist_repo=track_artist_repo,
                    )
                    await session.commit()
                    if created:
                        stats.imported_tracks += 1
                    else:
                        stats.updated_tracks += 1
                except Exception as exc:
                    await session.rollback()
                    append_error(
                        stats=stats,
                        service_track_id=index_item.service_track_id,
                        stage="storage-or-db-upsert",
                        error_type=type(exc).__name__,
                        message=str(exc),
                        with_traceback=True,
                    )
                    if settings.fail_on_error:
                        break

        finalize_stats(stats)
        write_report(stats=stats, report_path=settings.report_path)
        return stats

    async def clear_uploaded_files(self, settings: DbLoaderSettingsDTO) -> LoaderCleanupResult:
        index_items = read_dataset_index(settings.dataset_dir)
        cleanup = LoaderCleanupResult()

        for index_item in index_items:
            try:
                card = read_track_card(settings.dataset_dir, index_item)
                audio_path = self._resolve_audio_path(
                    dataset_dir=settings.dataset_dir,
                    index_audio_path=index_item.audio_path,
                    card_audio_path=card.local_paths.audio_path,
                )
                image_path = resolve_local_artifact_path(
                    dataset_dir=settings.dataset_dir,
                    raw_path=card.local_paths.image_path,
                    fallback_subdir="track_image",
                )
                bundle = map_card_to_import_bundle(
                    index_item=index_item,
                    card=card,
                    resolved_audio_path=audio_path,
                    resolved_image_path=image_path,
                )
            except Exception:
                cleanup.errors += 1
                continue

            keys = [
                bundle.track.audio_storage_key,
                bundle.track.cover_storage_key,
            ]

            for object_key in keys:
                if not object_key:
                    continue
                cleanup.attempted += 1
                try:
                    exists = await self.storage_service.object_exists(object_key=object_key)
                    if not exists:
                        cleanup.missing += 1
                        continue
                    await self.storage_service.delete_object(object_key=object_key)
                    cleanup.deleted += 1
                except Exception:
                    cleanup.errors += 1

        return cleanup

    async def _upsert_bundle(
        self,
        *,
        bundle: TrackImportBundleDTO,
        track_repo: TrackRepos,
        yandex_repo: YandexTrackRepos,
        artist_repo: ArtistRepos,
        artist_link_repo: ArtistServiceLinkRepos,
        track_artist_repo: TrackArtistRepos,
    ) -> bool:
        yandex_meta = await yandex_repo.get_by_yandex_track_id(bundle.yandex_meta.yandex_track_id)

        created = False
        if yandex_meta is None:
            track = await track_repo.create_track(bundle.track)
            created = True
        else:
            track = await track_repo.get_track_by_id(yandex_meta.track_id)
            if track is None:
                track = await track_repo.create_track(bundle.track)
                created = True
            else:
                track = await track_repo.update_track(track, bundle.track)

        await yandex_repo.upsert_yandex_meta(track.id, bundle.yandex_meta)

        track_artist_links: list[TrackArtistLinkDTO] = []
        for artist in bundle.artists:
            existing_link = await artist_link_repo.get_by_service_id(
                StreamingService.YANDEX_MUSIC,
                artist.service_artist_id,
            )
            if existing_link is None:
                artist_entity = await artist_repo.create_artist_if_missing(artist.name)
                link_payload = ArtistServiceLinkUpsertDTO(
                    artist_id=artist_entity.id,
                    service=StreamingService.YANDEX_MUSIC,
                    service_artist_id=artist.service_artist_id,
                    service_artist_name=artist.name,
                    fetched_at=bundle.yandex_meta.provider_fetched_at,
                )
                created_link = await artist_link_repo.upsert_link(link_payload)
                artist_id = created_link.artist_id
            else:
                link_payload = ArtistServiceLinkUpsertDTO(
                    artist_id=existing_link.artist_id,
                    service=StreamingService.YANDEX_MUSIC,
                    service_artist_id=artist.service_artist_id,
                    service_artist_name=artist.name,
                    fetched_at=bundle.yandex_meta.provider_fetched_at,
                )
                updated_link = await artist_link_repo.upsert_link(link_payload)
                artist_id = updated_link.artist_id

            track_artist_links.append(
                TrackArtistLinkDTO(
                    track_id=track.id,
                    artist_id=artist_id,
                    artist_order=artist.order,
                    role=None,
                )
            )

        await track_artist_repo.replace_track_artists(track.id, track_artist_links)
        return created

    async def _upload_bundle_files(
        self,
        *,
        bundle: TrackImportBundleDTO,
        resolved_audio_path: Path | None,
        resolved_image_path: Path | None,
    ) -> None:
        if bundle.track.audio_storage_key and resolved_audio_path is not None:
            await self._upload_file_if_missing(
                object_key=bundle.track.audio_storage_key,
                source_path=resolved_audio_path,
                content_type=self._guess_content_type(resolved_audio_path),
            )

        if bundle.track.cover_storage_key and resolved_image_path is not None:
            await self._upload_file_if_missing(
                object_key=bundle.track.cover_storage_key,
                source_path=resolved_image_path,
                content_type=self._guess_content_type(resolved_image_path),
            )

    async def _upload_file_if_missing(
        self,
        *,
        object_key: str,
        source_path: Path,
        content_type: str | None,
    ) -> None:
        exists = await self.storage_service.object_exists(object_key=object_key)
        if exists:
            return
        payload = source_path.read_bytes()
        await self.storage_service.create_object(
            object_key=object_key,
            data=payload,
            content_type=content_type,
        )

    @staticmethod
    def _guess_content_type(path: Path) -> str | None:
        extension = path.suffix.lower()
        if extension == ".mp3":
            return "audio/mpeg"
        if extension == ".jpg":
            return "image/jpeg"
        if extension == ".jpeg":
            return "image/jpeg"
        if extension == ".png":
            return "image/png"
        if extension == ".webp":
            return "image/webp"
        return None

    @staticmethod
    def _is_mvp_valid(valid_for_mvp: bool, resolved_audio_path: Path | None) -> bool:
        return bool(valid_for_mvp) and resolved_audio_path is not None

    @staticmethod
    def _resolve_audio_path(
        *,
        dataset_dir: Path,
        index_audio_path: str | None,
        card_audio_path: str | None,
    ) -> Path | None:
        resolved_from_index = resolve_local_artifact_path(
            dataset_dir=dataset_dir,
            raw_path=index_audio_path,
            fallback_subdir="music",
        )
        if resolved_from_index is not None:
            return resolved_from_index

        return resolve_local_artifact_path(
            dataset_dir=dataset_dir,
            raw_path=card_audio_path,
            fallback_subdir="music",
        )
