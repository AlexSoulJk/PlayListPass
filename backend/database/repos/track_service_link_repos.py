from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.base import StreamingService
from database.models.models import TrackServiceLink


class TrackServiceLinkRepos:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_service_track_id(
        self,
        *,
        service: StreamingService,
        service_track_id: str,
    ) -> TrackServiceLink | None:
        query = select(TrackServiceLink).where(
            TrackServiceLink.service == service,
            TrackServiceLink.service_track_id == service_track_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def upsert_link(
        self,
        *,
        track_id: int,
        service: StreamingService,
        service_track_id: str,
        external_url: str | None = None,
        cover_url: str | None = None,
        duration_sec: int | None = None,
        imported_from_search: bool = False,
        fetched_at: datetime | None = None,
    ) -> TrackServiceLink:
        existing = await self.get_by_service_track_id(
            service=service,
            service_track_id=service_track_id,
        )
        if existing is None:
            created = TrackServiceLink(
                track_id=track_id,
                service=service,
                service_track_id=service_track_id,
                external_url=external_url,
                cover_url=cover_url,
                duration_sec=duration_sec,
                imported_from_search=imported_from_search,
                fetched_at=fetched_at,
            )
            self.session.add(created)
            await self.session.flush()
            await self.session.refresh(created)
            return created

        existing.track_id = track_id
        if external_url is not None:
            existing.external_url = external_url
        if cover_url is not None:
            existing.cover_url = cover_url
        if duration_sec is not None:
            existing.duration_sec = duration_sec
        if imported_from_search:
            existing.imported_from_search = True
        if fetched_at is not None:
            existing.fetched_at = fetched_at
        await self.session.flush()
        await self.session.refresh(existing)
        return existing
