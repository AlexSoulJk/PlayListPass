from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.repos.playlist_repos import PlaylistRepos
from database.session import get_async_session
from routes.deps.group_deps import get_group_manager
from services.group import GroupManager
from services.search import SearchManager


async def get_search_repos(session: AsyncSession = Depends(get_async_session)) -> PlaylistRepos:
    return PlaylistRepos(session=session)


async def get_search_manager(
    repos: PlaylistRepos = Depends(get_search_repos),
    group_manager: GroupManager = Depends(get_group_manager),
) -> SearchManager:
    return SearchManager(
        playlist_repository=repos,
        group_manager=group_manager,
        session=repos.session,
    )
