import uuid
from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.models import Playlist, PlaylistTrack


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
