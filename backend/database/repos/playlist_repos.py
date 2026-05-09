import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.models import Playlist


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
