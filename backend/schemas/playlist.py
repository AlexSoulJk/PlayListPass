import uuid

from pydantic import BaseModel, ConfigDict, Field


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
