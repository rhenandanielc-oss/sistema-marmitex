import logging
import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.core.request_context import RequestInfo, set_request_info

logger = logging.getLogger("app.request")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(
        title="Marmitex B2B — API",
        description="Gestão de vendas B2B de marmitex e controle financeiro.",
        version="0.1.0",
        docs_url="/api/docs" if settings.api_docs_enabled else None,
        redoc_url="/api/redoc" if settings.api_docs_enabled else None,
        openapi_url="/api/openapi.json" if settings.api_docs_enabled else None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_request_info(RequestInfo(
            request_id=request_id[:64],
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        ))
        started = time.perf_counter()
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id[:64]
        logger.info("request", extra={"extra_fields": {
            "method": request.method, "path": request.url.path, "status": response.status_code,
            "duration_ms": round((time.perf_counter() - started) * 1000, 1)}})
        return response

    register_error_handlers(app)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
