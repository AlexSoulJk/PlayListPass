from __future__ import annotations

from dataclasses import dataclass
from math import ceil
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.base import StreamingService
from database.models.models import Group, Track, TrackServiceLink, User, UserCredential
from database.repos.playlist_repos import PlaylistRepos
from schemas.search import (
    SearchTrackItemResponse,
    SearchTracksPaginationResponse,
    SearchTracksRequest,
    SearchTracksResponse,
)
from services.group import GroupManager
from services.storage.base import StorageServiceBase


@dataclass(slots=True)
class _ServiceTrackMapping:
    service: StreamingService
    service_track_id: str
    external_url: str | None
    cover_url: str | None
    duration_sec: int | None


class SearchManager:
    def __init__(
        self,
        *,
        playlist_repository: PlaylistRepos,
        group_manager: GroupManager,
        session: AsyncSession,
    ) -> None:
        self.playlist_repository = playlist_repository
        self.group_manager = group_manager
        self.session = session

    async def search_tracks(
        self,
        *,
        user: User,
        payload: SearchTracksRequest,
        storage_service: StorageServiceBase,
    ) -> SearchTracksResponse:
        group = await self.group_manager.get_group_or_404(group_id=payload.group_id)
        await self.group_manager.get_member_connection_or_403(user=user, group=group)

        tracks = await self.playlist_repository.list_tracks_for_search(
            query_text=payload.query,
            services=payload.services,
        )

        all_items: list[SearchTrackItemResponse] = []
        for track in tracks:
            artist_label = self._resolve_artist_label(track)
            for mapping in self._build_mappings(track):
                if payload.services and mapping.service not in payload.services:
                    continue
                all_items.append(
                    SearchTrackItemResponse(
                        service=mapping.service,
                        service_track_id=mapping.service_track_id,
                        internal_track_id=track.id,
                        is_in_db=True,
                        title=track.title,
                        artist=artist_label,
                        cover_url=self._resolve_cover_url(
                            track=track,
                            mapping=mapping,
                            storage_service=storage_service,
                        ),
                        external_url=mapping.external_url,
                        duration_sec=mapping.duration_sec if mapping.duration_sec is not None else track.duration,
                    )
                )

        deduped_items = self._dedupe_items(all_items)
        total = len(deduped_items)
        pages = ceil(total / payload.page_size) if total else 1
        page = min(payload.page, pages)
        start = (page - 1) * payload.page_size
        end = start + payload.page_size
        paged_items = deduped_items[start:end]

        return SearchTracksResponse(
            items=paged_items,
            pagination=SearchTracksPaginationResponse(
                page=page,
                page_size=payload.page_size,
                total=total,
                pages=pages,
            ),
            service_availability=await self._resolve_service_availability(
                user_id=user.id,
                group=group,
            ),
        )

    async def _resolve_service_availability(
        self,
        *,
        user_id: uuid.UUID,
        group: Group,
    ) -> dict[StreamingService, bool]:
        # Yandex dataset is local, so we keep it enabled for group members by default.
        availability: dict[StreamingService, bool] = {
            StreamingService.YANDEX_MUSIC: True,
            StreamingService.SPOTIFY: False,
            StreamingService.YOUTUBE: False,
        }
        query = select(UserCredential.service).where(UserCredential.user_id == user_id)
        result = await self.session.execute(query)
        for service in result.scalars().all():
            availability[service] = True

        # Defensive check: if user lost access between calls, hide actions.
        member_connection = await self.group_manager.repos.get_user_connection(
            user_id=user_id,
            group_id=group.id,
        )
        if member_connection is None:
            return {service: False for service in availability}
        return availability

    @staticmethod
    def _resolve_artist_label(track: Track) -> str:
        if not track.track_artists:
            return "Unknown artist"
        sorted_links = sorted(
            track.track_artists,
            key=lambda link: (link.artist_order if link.artist_order is not None else 999, str(link.artist_id)),
        )
        names = [link.artist.name for link in sorted_links if link.artist is not None and link.artist.name]
        return ", ".join(names) if names else "Unknown artist"

    @staticmethod
    def _build_mappings(track: Track) -> list[_ServiceTrackMapping]:
        mappings: list[_ServiceTrackMapping] = []

        for link in track.service_links:
            mappings.append(
                _ServiceTrackMapping(
                    service=link.service,
                    service_track_id=link.service_track_id,
                    external_url=link.external_url,
                    cover_url=link.cover_url,
                    duration_sec=link.duration_sec,
                )
            )

        if track.yandex_meta is not None and track.yandex_meta.yandex_track_id:
            mappings.append(
                _ServiceTrackMapping(
                    service=StreamingService.YANDEX_MUSIC,
                    service_track_id=track.yandex_meta.yandex_track_id,
                    external_url=track.external_url,
                    cover_url=None,
                    duration_sec=track.duration,
                )
            )

        if not mappings:
            mappings.append(
                _ServiceTrackMapping(
                    service=track.service,
                    service_track_id=str(track.id),
                    external_url=track.external_url,
                    cover_url=None,
                    duration_sec=track.duration,
                )
            )
        return mappings

    @staticmethod
    def _resolve_cover_url(
        *,
        track: Track,
        mapping: _ServiceTrackMapping,
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
    def _dedupe_items(items: list[SearchTrackItemResponse]) -> list[SearchTrackItemResponse]:
        by_key: dict[tuple[str, str, int | None], SearchTrackItemResponse] = {}
        for item in items:
            key = (item.service.value, item.service_track_id, item.internal_track_id)
            by_key[key] = item
        return sorted(
            by_key.values(),
            key=lambda value: (value.title.lower(), value.artist.lower(), value.service_track_id),
        )
