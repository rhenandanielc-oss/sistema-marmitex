from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.core.permissions import AdminUser, DbSession
from app.schemas.common import Page, SortOrder
from app.schemas.user import PasswordReset, UserCreate, UserRead, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Usuários"])


@router.get("", response_model=Page[UserRead], summary="Lista usuários")
def list_users(
    admin: AdminUser, db: DbSession,
    q: str | None = None, active: bool | None = None,
    sort: str | None = None, order: SortOrder = "asc",
    page: Annotated[int, Query(ge=1)] = 1, page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Page[UserRead]:
    items, total = user_service.list_users(db, q=q, active=active, sort=sort, order=order, page=page,
                                           page_size=page_size)
    return Page.build([UserRead.model_validate(u) for u in items], total, page, page_size)


@router.post("", response_model=UserRead, status_code=201, summary="Cria usuário ADMIN")
def create_user(data: UserCreate, admin: AdminUser, db: DbSession) -> UserRead:
    return UserRead.model_validate(user_service.create_user(db, data, admin))


@router.get("/{user_id}", response_model=UserRead, summary="Detalhe do usuário")
def get_user(user_id: int, admin: AdminUser, db: DbSession) -> UserRead:
    from app.models import User
    from app.services.common import get_or_404

    return UserRead.model_validate(get_or_404(db, User, user_id, user_service.NOT_FOUND))


@router.patch("/{user_id}", response_model=UserRead, summary="Edita usuário")
def update_user(user_id: int, data: UserUpdate, admin: AdminUser, db: DbSession) -> UserRead:
    return UserRead.model_validate(user_service.update_user(db, user_id, data, admin))


@router.post("/{user_id}/activate", response_model=UserRead, summary="Ativa usuário")
def activate_user(user_id: int, admin: AdminUser, db: DbSession) -> UserRead:
    return UserRead.model_validate(user_service.set_user_active(db, user_id, True, admin))


@router.post("/{user_id}/deactivate", response_model=UserRead, summary="Desativa usuário")
def deactivate_user(user_id: int, admin: AdminUser, db: DbSession) -> UserRead:
    return UserRead.model_validate(user_service.set_user_active(db, user_id, False, admin))


@router.post("/{user_id}/reset-password", status_code=204, summary="Redefine a senha de um usuário")
def reset_password(user_id: int, data: PasswordReset, admin: AdminUser, db: DbSession) -> Response:
    user_service.reset_password(db, user_id, data.new_password, admin)
    return Response(status_code=204)
