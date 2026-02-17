from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from database.models.base import UserRole, StreamingService
# Base schema with common fields
class UserBase(BaseModel):
    name: str = Field(..., max_length=255, description="User's full name")
    role: UserRole = Field(default=UserRole.VIEWER, description="User's role in the system")
# Schema for creating a new user
class UserCreate(UserBase):
    pass
# Schema for updating user data
class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255, description="User's full name")
    role: Optional[UserRole] = Field(None, description="User's role in the system")
# Schema for reading user data (includes all fields)
class User(UserBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True  # Enables ORM mode for SQLAlchemy models
# Schema for user credentials
class UserCredentialBase(BaseModel):
    service: StreamingService
    token: str
    expiry: Optional[datetime] = None
class UserCredentialCreate(UserCredentialBase):
    pass
class UserCredential(UserCredentialBase):
    id: int
    user_id: UUID
    created_at: datetime
    class Config:
        from_attributes = True
# Schema for user with relationships
class UserWithRelationships(User):
    credentials: List[UserCredential] = Field(
        default_factory=list,
        description="User's credentials for external services"
    )
# Schema for user login response
class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User
# Schema for token data
class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[UUID] = None

