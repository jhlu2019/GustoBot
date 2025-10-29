from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Shared fields for user payloads."""

    username: str
    email: EmailStr


class UserCreate(UserBase):
    """Payload for creating a new user."""

    password: str


class UserUpdate(BaseModel):
    """Payload for updating an existing user."""

    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    status: Optional[str] = None


class UserLogin(BaseModel):
    """Login request payload."""

    email: EmailStr
    password: str


class UserResponse(UserBase):
    """User model returned to clients."""

    id: int
    status: str
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Authentication token response."""

    access_token: str
    token_type: str = "bearer"
