import uuid

from fastapi import APIRouter, Depends, status

from database.models.models import Group, User
from routes.deps.group_deps import (
    get_current_active_user,
    get_group_from_path,
    get_group_manager,
    get_group_maintainer_connection,
    get_group_member_connection,
)
from schemas.group import (
    GroupCreateRequest,
    GroupDeleteResponse,
    GroupListItemResponse,
    GroupPlaylistItemResponse,
    GroupQrResponse,
    GroupUpdateRequest,
    GroupUserItemResponse,
    GroupUserRoleUpdateRequest,
)
from services.group import GroupManager


group_router = APIRouter(prefix="/groups", tags=["Groups"])


@group_router.get("/", response_model=list[GroupListItemResponse], name="get_group_list")
async def get_group_list(
    user: User = Depends(get_current_active_user),
    manager: GroupManager = Depends(get_group_manager),
) -> list[GroupListItemResponse]:
    return await manager.get_group_list(user=user)


@group_router.get(
    "/{group_id}/playlists",
    response_model=list[GroupPlaylistItemResponse],
    name="get_group_playlist",
)
async def get_group_playlist(
    user: User = Depends(get_current_active_user),
    group: Group = Depends(get_group_from_path),
    _: object = Depends(get_group_member_connection),
    manager: GroupManager = Depends(get_group_manager),
) -> list[GroupPlaylistItemResponse]:
    return await manager.get_group_playlist(user=user, group=group)


@group_router.get("/{group_id}/qr", response_model=GroupQrResponse, name="get_group_qr")
async def get_group_qr(
    user: User = Depends(get_current_active_user),
    group: Group = Depends(get_group_from_path),
    _: object = Depends(get_group_member_connection),
    manager: GroupManager = Depends(get_group_manager),
) -> GroupQrResponse:
    return await manager.get_group_qr(user=user, group=group)


@group_router.get(
    "/{group_id}/users",
    response_model=list[GroupUserItemResponse],
    name="get_group_users",
)
async def get_group_users(
    user: User = Depends(get_current_active_user),
    group: Group = Depends(get_group_from_path),
    _: object = Depends(get_group_member_connection),
    manager: GroupManager = Depends(get_group_manager),
) -> list[GroupUserItemResponse]:
    return await manager.get_group_users(user=user, group=group)


@group_router.post(
    "/",
    response_model=GroupListItemResponse,
    status_code=status.HTTP_201_CREATED,
    name="create_group",
)
async def create_group(
    payload: GroupCreateRequest,
    user: User = Depends(get_current_active_user),
    manager: GroupManager = Depends(get_group_manager),
) -> GroupListItemResponse:
    return await manager.create_group(user=user, payload=payload)


@group_router.patch("/{group_id}", response_model=GroupListItemResponse, name="update_group_info")
async def update_group_info(
    payload: GroupUpdateRequest,
    user: User = Depends(get_current_active_user),
    group: Group = Depends(get_group_from_path),
    _: object = Depends(get_group_maintainer_connection),
    manager: GroupManager = Depends(get_group_manager),
) -> GroupListItemResponse:
    return await manager.update_group_info(user=user, group=group, payload=payload)


@group_router.patch(
    "/{group_id}/users/{target_user_id}/role",
    response_model=GroupUserItemResponse,
    name="change_group_user_list",
)
async def change_group_user_list(
    target_user_id: uuid.UUID,
    payload: GroupUserRoleUpdateRequest,
    user: User = Depends(get_current_active_user),
    group: Group = Depends(get_group_from_path),
    _: object = Depends(get_group_maintainer_connection),
    manager: GroupManager = Depends(get_group_manager),
) -> GroupUserItemResponse:
    return await manager.change_group_user_list(
        user=user,
        group=group,
        target_user_id=target_user_id,
        payload=payload,
    )


@group_router.delete(
    "/{group_id}",
    response_model=GroupDeleteResponse,
    status_code=status.HTTP_200_OK,
    name="delete_group",
)
async def delete_group(
    group_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    group: Group = Depends(get_group_from_path),
    _: object = Depends(get_group_maintainer_connection),
    manager: GroupManager = Depends(get_group_manager),
) -> GroupDeleteResponse:
    await manager.delete_group(user=user, group=group)
    return GroupDeleteResponse(group_id=group_id)
