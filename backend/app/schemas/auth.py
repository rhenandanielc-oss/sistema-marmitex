from datetime import datetime

from pydantic import Field

from app.schemas.common import InputModel, OutputModel


class LoginIn(InputModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=200)


class UserMe(OutputModel):
    id: int
    name: str
    email: str
    role: str


class LoginOut(OutputModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: UserMe


class ChangePasswordIn(InputModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=8, max_length=200)
