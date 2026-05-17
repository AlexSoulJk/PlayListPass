import uuid

from pydantic import BaseModel, Field

from database.models.base import StreamingService


class SearchTracksRequest(BaseModel):
    group_id: uuid.UUID
    query: str = Field(min_length=1, max_length=255)
    services: list[StreamingService] = Field(default_factory=list)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=8, ge=1, le=50)


class SearchTrackItemResponse(BaseModel):
    service: StreamingService
    service_track_id: str
    internal_track_id: int | None = None
    is_in_db: bool
    title: str
    artist: str
    cover_url: str | None = None
    external_url: str | None = None
    duration_sec: int | None = None


class SearchTracksPaginationResponse(BaseModel):
    page: int
    page_size: int
    total: int
    pages: int


class SearchTracksResponse(BaseModel):
    items: list[SearchTrackItemResponse]
    pagination: SearchTracksPaginationResponse
    service_availability: dict[StreamingService, bool]
