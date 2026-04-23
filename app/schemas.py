from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    uuid: str
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MediaFileResponse(BaseModel):
    id: int
    file_id: str
    original_filename: str
    media_type: str
    mime_type: str
    file_size: int
    width: Optional[int]
    height: Optional[int]
    view_count: int
    created_at: datetime
    updated_at: Optional[datetime]

    expires_at: Optional[datetime]
    is_expired: bool
    is_deleted: bool
    deleted_at: Optional[datetime]

    original_url: str
    standard_url: Optional[str]
    low_url: Optional[str]
    icon_url: Optional[str]

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    success: bool
    message: str
    file: Optional[MediaFileResponse] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
