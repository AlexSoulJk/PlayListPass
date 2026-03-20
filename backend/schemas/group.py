import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from database.models.base import UserRole


class GroupCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=1000)
    is_public: bool = True


class GroupUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=1000)
    image_url: str | None = None


class GroupListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    image_url: str | None
    is_public: bool


class GroupPlaylistItemResponse(BaseModel):
    id: uuid.UUID
    name: str
    image_url: str | None
    track_count: int = Field(ge=0)


class GroupQrResponse(BaseModel):
    group_id: uuid.UUID
    qr_url: str
    expired_at: datetime
    is_expired: bool


class GroupUserItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    name: str
    role: UserRole


class GroupMutableRole(str, Enum):
    GUEST = "GUEST"
    VIEWER = "VIEWER"


class GroupUserRoleUpdateRequest(BaseModel):
    role: GroupMutableRole

    @property
    def as_user_role(self) -> UserRole:
        return UserRole(self.role.value)


class GroupDeleteResponse(BaseModel):
    status: str = "deleted"
    group_id: uuid.UUID
