import uuid

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.models import Connection, Group, User
from database.repos.group_repos import GroupRepos
from database.session import get_async_session
from services.auth import fastapi_users
from services.group import GroupManager


async def get_group_repos(session: AsyncSession = Depends(get_async_session)) -> GroupRepos:
    return GroupRepos(session=session)


async def get_group_manager(repos: GroupRepos = Depends(get_group_repos)) -> GroupManager:
    return GroupManager(repos=repos)


async def get_current_active_user(user: User = Depends(fastapi_users.current_user(active=True))) -> User:
    return user


async def get_group_from_path(
    group_id: uuid.UUID,
    manager: GroupManager = Depends(get_group_manager),
) -> Group:
    return await manager.get_group_or_404(group_id=group_id)


async def get_group_member_connection(
    user: User = Depends(get_current_active_user),
    group: Group = Depends(get_group_from_path),
    manager: GroupManager = Depends(get_group_manager),
) -> Connection:
    return await manager.get_member_connection_or_403(user=user, group=group)


async def get_group_maintainer_connection(
    user: User = Depends(get_current_active_user),
    group: Group = Depends(get_group_from_path),
    manager: GroupManager = Depends(get_group_manager),
) -> Connection:
    return await manager.get_maintainer_connection_or_403(user=user, group=group)
