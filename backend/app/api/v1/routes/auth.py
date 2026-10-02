from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.core.permissions import CurrentUser, DbSession, get_current_user
from app.schemas.auth import ChangePasswordIn, LoginIn, LoginOut, UserMe
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Autenticação"])

Current = Annotated[CurrentUser, Depends(get_current_user)]


@router.post("/login", response_model=LoginOut, summary="Login com e-mail e senha")
def login(data: LoginIn, db: DbSession) -> LoginOut:
    result = auth_service.login(db, data.email, data.password)
    return LoginOut(access_token=result.access_token, expires_at=result.expires_at,
                    user=UserMe.model_validate(result.user))


@router.post("/logout", status_code=204, summary="Encerra a sessão atual")
def logout(current: Current, db: DbSession) -> Response:
    auth_service.logout(db, current)
    return Response(status_code=204)


@router.get("/me", response_model=UserMe, summary="Usuário autenticado")
def me(current: Current) -> UserMe:
    return UserMe.model_validate(current.user)


@router.post("/change-password", status_code=204, summary="Altera a própria senha")
def change_password(data: ChangePasswordIn, current: Current, db: DbSession) -> Response:
    auth_service.change_password(db, current, data.current_password, data.new_password)
    return Response(status_code=204)
