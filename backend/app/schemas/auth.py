from pydantic import BaseModel, EmailStr
from typing import Optional
from ..models.user import UserRole


class Token(BaseModel):
    access_token: str
    token_type: str
    user: "UserResponse"


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    password: str
    role: UserRole
    bio: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    profile_picture: Optional[str] = None
    bio: Optional[str] = None

    class Config:
        from_attributes = True


# Forward reference resolution
Token.model_rebuild()
