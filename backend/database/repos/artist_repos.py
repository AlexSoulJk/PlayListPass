from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.yandex_service.databaseloder.dto import ArtistUpsertDTO
from database.models.models import Artist


class ArtistRepos:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_artist_if_missing(self, name: str) -> Artist:
        query = select(Artist).where(Artist.name == name).order_by(Artist.id.asc())
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()
        if existing is not None:
            return existing

        payload = ArtistUpsertDTO(name=name)
        artist = Artist(name=payload.name)
        self.session.add(artist)
        await self.session.flush()
        await self.session.refresh(artist)
        return artist

    async def get_artist_by_id(self, artist_id: uuid.UUID) -> Artist | None:
        return await self.session.get(Artist, artist_id)
