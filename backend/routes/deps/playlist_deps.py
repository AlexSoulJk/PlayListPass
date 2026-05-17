import uuid

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.models import Playlist
from database.repos.playlist_repos import PlaylistRepos
from database.session import get_async_session
from services.playlist import PlayListManager


async def get_playlist_repos(session: AsyncSession = Depends(get_async_session)) -> PlaylistRepos:
    return PlaylistRepos(session=session)


async def get_playlist_manager(repos: PlaylistRepos = Depends(get_playlist_repos)) -> PlayListManager:
    return PlayListManager(playlist_repository=repos)


async def get_playlist_from_path(
    playlist_id: uuid.UUID,
    manager: PlayListManager = Depends(get_playlist_manager),
) -> Playlist:
    return await manager.get_playlist_or_404(playlist_id=playlist_id)
