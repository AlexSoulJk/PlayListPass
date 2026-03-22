from pydantic import BaseModel, Field

from services.storage.types import StorageEntity, StorageFileFormat


class StorageUploadInitRequest(BaseModel):
    entity: StorageEntity
    file_format: StorageFileFormat
    filename: str | None = Field(default=None, max_length=512)
    content_type: str | None = Field(default=None, max_length=255)


class StorageUploadInitResponse(BaseModel):
    object_key: str
    upload_url: str
    file_url: str
    expires_in_seconds: int


class StorageDeleteResponse(BaseModel):
    status: str = "deleted"
    object_key: str
