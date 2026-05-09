from fastapi import APIRouter, Depends, status

from database.models.models import Group, User
from routes.deps.playlist_deps import get_playlist_manager
from routes.deps.group_deps import (
    get_current_active_user,
    get_group_from_path,
    get_group_maintainer_connection,
)
from schemas.playlist import (
    PlaylistCreateRequest,
    PlaylistItemResponse,
)
from services.playlist import PlayListManager


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
