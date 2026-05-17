import uuid

from pydantic import BaseModel, ConfigDict, Field

from database.models.base import StreamingService


class PlaylistCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    image_url: str | None = Field(default=None, max_length=2048)


class PlaylistUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class PlaylistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    image_url: str | None


class PlaylistDeleteResponse(BaseModel):
    status: str = "deleted"
    playlist_id: uuid.UUID


class PlaylistImageUploadInitRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=512)
    content_type: str | None = Field(default=None, max_length=255)


class PlaylistImageUploadInitResponse(BaseModel):
    object_key: str
    upload_url: str
    file_url: str
    expires_in_seconds: int


class PlaylistImageCommitRequest(BaseModel):
    object_key: str = Field(min_length=1, max_length=2048)
    image_url: str | None = Field(default=None, max_length=2048)


class PlaylistImageDeleteResponse(BaseModel):
    status: str = "deleted"
    playlist_id: uuid.UUID


class PlaylistTrackAddRequest(BaseModel):
    internal_track_id: int | None = Field(default=None, ge=1)
    service: StreamingService | None = None
    service_track_id: str | None = Field(default=None, min_length=1, max_length=191)
    title: str | None = Field(default=None, min_length=1, max_length=512)
    artist: str | None = Field(default=None, min_length=1, max_length=255)
    cover_url: str | None = Field(default=None, max_length=2048)
    external_url: str | None = Field(default=None, max_length=2048)
    duration_sec: int | None = Field(default=None, ge=0)
    imported_from_search: bool = True


class PlaylistTrackAddResponse(BaseModel):
    status: str = "added"
    playlist_id: uuid.UUID
    track_id: int
    created_new_track: bool


class PlaylistTrackDeleteResponse(BaseModel):
    status: str = "deleted"
    playlist_id: uuid.UUID
    track_id: int


class PlaylistTrackItemResponse(BaseModel):
    track_id: int
    title: str
    artist: str
    service: StreamingService
    service_track_id: str
    cover_url: str | None = None
    external_url: str | None = None
    duration_sec: int | None = None


class PlaylistTracksResponse(BaseModel):
    playlist_id: uuid.UUID
    items: list[PlaylistTrackItemResponse]


class PlaylistPlaybackTrackResponse(BaseModel):
    playlist_id: uuid.UUID
    track_id: int
    title: str
    artist: str
    service: StreamingService
    service_track_id: str
    cover_url: str | None = None
    external_url: str | None = None
    duration_sec: int | None = None
    audio_url: str


class PlaylistPlaybackQueueResponse(BaseModel):
    playlist_id: uuid.UUID
    items: list[PlaylistPlaybackTrackResponse]
