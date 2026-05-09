from pydantic import BaseModel, ConfigDict, Field
import uuid

class PlaylistCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=1000)
    image_url: str | None = None

class PlaylistItemResponse(BaseModel):
    id: uuid.UUID
    name: str
    image_url: str | None