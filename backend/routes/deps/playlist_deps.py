from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_async_session
from database.repos.playlist_repos import PlaylistRepos
from fastapi import Depends
from services.playlist import PlayListManager


async def get_playlist_repos(session: AsyncSession = Depends(get_async_session)) -> PlaylistRepos:
    return PlaylistRepos(session=session)


async def get_playlist_manager(repos: PlaylistRepos = Depends(get_playlist_repos)) -> PlayListManager:
    return PlayListManager(playlist_repository=repos)
