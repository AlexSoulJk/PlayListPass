import uuid

from fastapi import APIRouter, Depends, status

from database.models.models import Group, Playlist, User
from routes.deps.group_deps import (
    get_current_active_user,
    get_group_from_path,
    get_group_maintainer_connection,
)
from routes.deps.playlist_deps import get_playlist_from_path, get_playlist_manager
from routes.deps.storage_deps import get_storage_service
from schemas.playlist import (
    PlaylistCreateRequest,
    PlaylistDeleteResponse,
    PlaylistImageCommitRequest,
    PlaylistImageDeleteResponse,
    PlaylistImageUploadInitRequest,
    PlaylistImageUploadInitResponse,
    PlaylistItemResponse,
    PlaylistUpdateRequest,
)
from services.playlist import PlayListManager
from services.storage.base import StorageServiceBase


playlist_router = APIRouter(prefix="/playlist", tags=["Playlists"])


@playlist_router.post(
    "/{group_id}/create",
    response_model=PlaylistItemResponse,
    status_code=status.HTTP_201_CREATED,
    name="create_playlist",
)
async def create_playlist(
    payload: PlaylistCreateRequest,
    user: User = Depends(get_current_active_user),
    group: Group = Depends(get_group_from_path),
    _: object = Depends(get_group_maintainer_connection),
    playlist_manager: PlayListManager = Depends(get_playlist_manager),
) -> PlaylistItemResponse:
    return await playlist_manager.create_playlist(user=user, payload=payload, group=group)


@playlist_router.patch(
    "/{group_id}/{playlist_id}",
    response_model=PlaylistItemResponse,
    name="update_playlist",
)
async def update_playlist(
    playlist_id: uuid.UUID,
    payload: PlaylistUpdateRequest,
    user: User = Depends(get_current_active_user),
    group: Group = Depends(get_group_from_path),
    _: object = Depends(get_group_maintainer_connection),
    playlist: Playlist = Depends(get_playlist_from_path),
    playlist_manager: PlayListManager = Depends(get_playlist_manager),
) -> PlaylistItemResponse:
    return await playlist_manager.update_playlist(
        user=user,
        group=group,
        playlist=playlist,
        payload=payload,
    )


@playlist_router.post(
    "/{group_id}/{playlist_id}/image/upload-init",
    response_model=PlaylistImageUploadInitResponse,
    name="init_playlist_image_upload",
)
async def init_playlist_image_upload(
    playlist_id: uuid.UUID,
    payload: PlaylistImageUploadInitRequest,
    user: User = Depends(get_current_active_user),
    group: Group = Depends(get_group_from_path),
    _: object = Depends(get_group_maintainer_connection),
    playlist: Playlist = Depends(get_playlist_from_path),
    playlist_manager: PlayListManager = Depends(get_playlist_manager),
    storage_service: StorageServiceBase = Depends(get_storage_service),
) -> PlaylistImageUploadInitResponse:
    return await playlist_manager.init_playlist_image_upload(
        user=user,
        group=group,
        playlist=playlist,
        payload=payload,
        storage_service=storage_service,
    )


@playlist_router.post(
    "/{group_id}/{playlist_id}/image/commit",
    response_model=PlaylistItemResponse,
    name="commit_playlist_image_upload",
)
async def commit_playlist_image_upload(
    playlist_id: uuid.UUID,
    payload: PlaylistImageCommitRequest,
    user: User = Depends(get_current_active_user),
    group: Group = Depends(get_group_from_path),
    _: object = Depends(get_group_maintainer_connection),
    playlist: Playlist = Depends(get_playlist_from_path),
    playlist_manager: PlayListManager = Depends(get_playlist_manager),
    storage_service: StorageServiceBase = Depends(get_storage_service),
) -> PlaylistItemResponse:
    return await playlist_manager.commit_playlist_image_upload(
        user=user,
        group=group,
        playlist=playlist,
        payload=payload,
        storage_service=storage_service,
    )


@playlist_router.delete(
    "/{group_id}/{playlist_id}/image",
    response_model=PlaylistImageDeleteResponse,
    name="delete_playlist_image",
)
async def delete_playlist_image(
    playlist_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    group: Group = Depends(get_group_from_path),
    _: object = Depends(get_group_maintainer_connection),
    playlist: Playlist = Depends(get_playlist_from_path),
    playlist_manager: PlayListManager = Depends(get_playlist_manager),
    storage_service: StorageServiceBase = Depends(get_storage_service),
) -> PlaylistImageDeleteResponse:
    return await playlist_manager.delete_playlist_image(
        user=user,
        group=group,
        playlist=playlist,
        storage_service=storage_service,
    )


@playlist_router.delete(
    "/{group_id}/{playlist_id}",
    response_model=PlaylistDeleteResponse,
    status_code=status.HTTP_200_OK,
    name="delete_playlist",
)
async def delete_playlist(
    playlist_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    group: Group = Depends(get_group_from_path),
    _: object = Depends(get_group_maintainer_connection),
    playlist: Playlist = Depends(get_playlist_from_path),
    playlist_manager: PlayListManager = Depends(get_playlist_manager),
    storage_service: StorageServiceBase = Depends(get_storage_service),
) -> PlaylistDeleteResponse:
    return await playlist_manager.delete_playlist(
        user=user,
        group=group,
        playlist=playlist,
        storage_service=storage_service,
    )
