from fastapi import APIRouter, Depends

from database.models.models import User
from routes.deps.group_deps import get_current_active_user
from routes.deps.search_deps import get_search_manager
from routes.deps.storage_deps import get_storage_service
from schemas.search import SearchTracksRequest, SearchTracksResponse
from services.search import SearchManager
from services.storage.base import StorageServiceBase


search_router = APIRouter(prefix="/search", tags=["Search"])


@search_router.post("/tracks", response_model=SearchTracksResponse, name="search_tracks")
async def search_tracks(
    payload: SearchTracksRequest,
    user: User = Depends(get_current_active_user),
    search_manager: SearchManager = Depends(get_search_manager),
    storage_service: StorageServiceBase = Depends(get_storage_service),
) -> SearchTracksResponse:
    return await search_manager.search_tracks(
        user=user,
        payload=payload,
        storage_service=storage_service,
    )
