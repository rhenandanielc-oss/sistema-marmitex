from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.permissions import DbSession

router = APIRouter(prefix="/health", tags=["Saúde"])


@router.get("/live", summary="Processo ativo")
def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", summary="Banco de dados acessível")
def ready(db: DbSession) -> JSONResponse:
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        return JSONResponse(status_code=503, content={"status": "unavailable", "database": "down"})
    return JSONResponse(content={"status": "ok", "database": "up"})
