import uuid
from typing import Optional

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.base import StreamingService
from database.models.models import (
    Artist,
    Playlist,
    PlaylistTrack,
    Track,
    TrackArtist,
    TrackServiceLink,
    YandexTrack,
)


class PlaylistRepos:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_playlist(
        self,
        *,
        playlist_name: str,
        group_id: uuid.UUID,
        image_url: Optional[str],
    ) -> Playlist:
        playlist = Playlist(
            name=playlist_name,
            group_id=group_id,
            image_url=image_url,
        )

        self.session.add(playlist)
        await self.session.commit()
        await self.session.refresh(playlist)
        return playlist

    async def get_playlist_by_id(self, playlist_id: uuid.UUID) -> Optional[Playlist]:
        return await self.session.get(Playlist, playlist_id)

    async def get_playlist_by_group_and_name(
        self,
        *,
        group_id: uuid.UUID,
        playlist_name: str,
        exclude_playlist_id: uuid.UUID | None = None,
    ) -> Optional[Playlist]:
        normalized_name = playlist_name.strip().lower()
        query = select(Playlist).where(
            Playlist.group_id == group_id,
            func.lower(Playlist.name) == normalized_name,
        )
        if exclude_playlist_id is not None:
            query = query.where(Playlist.id != exclude_playlist_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_playlist(
        self,
        playlist: Playlist,
        *,
        name: str | None = None,
    ) -> Playlist:
        if name is not None:
            playlist.name = name
        await self.session.commit()
        await self.session.refresh(playlist)
        return playlist

    async def update_playlist_image(self, playlist: Playlist, *, image_url: str | None) -> Playlist:
        playlist.image_url = image_url
        await self.session.commit()
        await self.session.refresh(playlist)
        return playlist

    async def delete_playlist(self, playlist_id: uuid.UUID) -> bool:
        playlist = await self.get_playlist_by_id(playlist_id=playlist_id)
        if playlist is None:
            return False

        await self.session.execute(
            delete(PlaylistTrack).where(PlaylistTrack.playlist_id == playlist_id)
        )
        await self.session.execute(
            delete(Playlist).where(Playlist.id == playlist_id)
        )
        await self.session.commit()
        return True

    async def rollback(self) -> None:
        await self.session.rollback()

    async def get_track_by_id(self, track_id: int) -> Track | None:
        query = (
            select(Track)
            .options(
                selectinload(Track.track_artists).selectinload(TrackArtist.artist),
                selectinload(Track.service_links),
                selectinload(Track.yandex_meta),
            )
            .where(Track.id == track_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_playlist_track_link(self, *, playlist_id: uuid.UUID, track_id: int) -> PlaylistTrack | None:
        query = select(PlaylistTrack).where(
            PlaylistTrack.playlist_id == playlist_id,
            PlaylistTrack.track_id == track_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def add_playlist_track_link(
        self,
        *,
        playlist_id: uuid.UUID,
        track_id: int,
        position: int | None = None,
    ) -> PlaylistTrack:
        link = PlaylistTrack(
            playlist_id=playlist_id,
            track_id=track_id,
            position=position,
        )
        self.session.add(link)
        await self.session.flush()
        await self.session.refresh(link)
        return link

    async def delete_playlist_track_link(self, *, playlist_id: uuid.UUID, track_id: int) -> bool:
        result = await self.session.execute(
            delete(PlaylistTrack).where(
                PlaylistTrack.playlist_id == playlist_id,
                PlaylistTrack.track_id == track_id,
            )
        )
        return (result.rowcount or 0) > 0

    async def list_playlist_tracks(self, *, playlist_id: uuid.UUID) -> list[PlaylistTrack]:
        query = (
            select(PlaylistTrack)
            .options(
                selectinload(PlaylistTrack.track)
                .selectinload(Track.track_artists)
                .selectinload(TrackArtist.artist),
                selectinload(PlaylistTrack.track).selectinload(Track.service_links),
                selectinload(PlaylistTrack.track).selectinload(Track.yandex_meta),
            )
            .where(PlaylistTrack.playlist_id == playlist_id)
            .order_by(
                PlaylistTrack.position.is_(None),
                PlaylistTrack.position.asc(),
                PlaylistTrack.added_at.asc(),
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_tracks_for_search(
        self,
        *,
        query_text: str,
        services: list[StreamingService],
    ) -> list[Track]:
        normalized_query = f"%{query_text.strip().lower()}%"
        query = (
            select(Track)
            .outerjoin(TrackArtist, TrackArtist.track_id == Track.id)
            .outerjoin(Artist, Artist.id == TrackArtist.artist_id)
            .outerjoin(TrackServiceLink, TrackServiceLink.track_id == Track.id)
            .outerjoin(YandexTrack, YandexTrack.track_id == Track.id)
            .options(
                selectinload(Track.track_artists).selectinload(TrackArtist.artist),
                selectinload(Track.service_links),
                selectinload(Track.yandex_meta),
            )
            .where(
                or_(
                    func.lower(Track.title).like(normalized_query),
                    func.lower(Artist.name).like(normalized_query),
                )
            )
            .distinct()
            .order_by(Track.added_at.desc())
        )

        if services:
            query = query.where(
                or_(
                    Track.service.in_(services),
                    TrackServiceLink.service.in_(services),
                    YandexTrack.yandex_track_id.is_not(None),
                )
            )

        result = await self.session.execute(query)
        return list(result.scalars().unique().all())
