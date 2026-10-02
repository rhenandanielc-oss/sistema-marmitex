from datetime import datetime

from pydantic import EmailStr, Field

from app.schemas.common import InputModel, OutputModel


class UserCreate(InputModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)


class UserUpdate(InputModel):
    name: str | None = Field(None, min_length=2, max_length=120)
    email: EmailStr | None = None
    version: int = Field(ge=1)


class PasswordReset(InputModel):
    new_password: str = Field(min_length=8, max_length=200)


class UserRead(OutputModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool
    last_login_at: datetime | None
    version: int
    created_at: datetime
