from __future__ import annotations

import uuid

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.yandex_service.databaseloder.dto import TrackArtistLinkDTO
from database.models.models import TrackArtist


class TrackArtistRepos:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_track_artist(
        self,
        track_id: int,
        artist_id: uuid.UUID,
        artist_order: int | None,
        role: str | None,
    ) -> TrackArtist:
        link_payload = TrackArtistLinkDTO(
            track_id=track_id,
            artist_id=artist_id,
            artist_order=artist_order,
            role=role,
        )
        link = TrackArtist(
            track_id=link_payload.track_id,
            artist_id=link_payload.artist_id,
            artist_order=link_payload.artist_order,
            role=link_payload.role,
        )
        self.session.add(link)
        await self.session.flush()
        await self.session.refresh(link)
        return link

    async def replace_track_artists(self, track_id: int, links: list[TrackArtistLinkDTO]) -> None:
        await self.session.execute(delete(TrackArtist).where(TrackArtist.track_id == track_id))

        seen_artists: set[uuid.UUID] = set()
        for link in links:
            if link.artist_id in seen_artists:
                continue
            seen_artists.add(link.artist_id)
            await self.upsert_track_artist(
                track_id=track_id,
                artist_id=link.artist_id,
                artist_order=link.artist_order,
                role=link.role,
            )
