from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.yandex_service.databaseloder.dto import ArtistServiceLinkUpsertDTO
from database.models.base import StreamingService
from database.models.models import ArtistServiceLink


class ArtistServiceLinkRepos:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_service_id(
        self,
        service: StreamingService,
        service_artist_id: str,
    ) -> ArtistServiceLink | None:
        query = select(ArtistServiceLink).where(
            ArtistServiceLink.service == service,
            ArtistServiceLink.service_artist_id == service_artist_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def upsert_link(self, payload: ArtistServiceLinkUpsertDTO) -> ArtistServiceLink:
        existing = await self.get_by_service_id(payload.service, payload.service_artist_id)
        if existing is None:
            if payload.artist_id is None:
                raise ValueError("artist_id is required to create ArtistServiceLink.")

            created = ArtistServiceLink(
                artist_id=payload.artist_id,
                service=payload.service,
                service_artist_id=payload.service_artist_id,
                service_artist_name=payload.service_artist_name,
                external_url=payload.external_url,
                fetched_at=payload.fetched_at,
            )
            self.session.add(created)
            await self.session.flush()
            await self.session.refresh(created)
            return created

        if payload.artist_id is not None:
            existing.artist_id = payload.artist_id
        existing.service_artist_name = payload.service_artist_name
        existing.external_url = payload.external_url
        existing.fetched_at = payload.fetched_at
        await self.session.flush()
        await self.session.refresh(existing)
        return existing
