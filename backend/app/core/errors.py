"""Erros de domínio e resposta de erro padronizada (API.md 1.4)."""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.request_context import get_request_id


class AppError(Exception):
    status_code = 400
    code = "BAD_REQUEST"
    message = "Requisição inválida."

    def __init__(self, message: str | None = None, details: list[dict[str, Any]] | None = None):
        super().__init__(message or self.message)
        self.message = message or self.message
        self.details = details or []


class Unauthenticated(AppError):
    status_code = 401
    code = "UNAUTHENTICATED"
    message = "Autenticação necessária."


class InvalidCredentials(AppError):
    status_code = 401
    code = "INVALID_CREDENTIALS"
    message = "E-mail ou senha inválidos."


class Forbidden(AppError):
    status_code = 403
    code = "FORBIDDEN"
    message = "Acesso negado."


class NotFound(AppError):
    status_code = 404
    code = "NOT_FOUND"
    message = "Registro não encontrado."


class Conflict(AppError):
    status_code = 409
    code = "CONFLICT"
    message = "Conflito com dados existentes."


class VersionConflict(AppError):
    status_code = 409
    code = "VERSION_CONFLICT"
    message = "O registro foi alterado por outra pessoa. Recarregue e tente novamente."


class ValidationFailed(AppError):
    status_code = 422
    code = "VALIDATION_ERROR"
    message = "Dados inválidos."

    def __init__(self, message: str | None = None, field: str | None = None,
                 details: list[dict[str, Any]] | None = None):
        if field and not details:
            details = [{"field": field, "message": message or self.message}]
        super().__init__(message, details)


class TooManyRequests(AppError):
    status_code = 429
    code = "TOO_MANY_REQUESTS"
    message = "Muitas tentativas. Aguarde alguns minutos e tente novamente."


def error_body(code: str, message: str, details: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details or [],
                      "request_id": get_request_id()}}


_PYDANTIC_MESSAGES = {
    "missing": "Campo obrigatório.",
    "extra_forbidden": "Campo não permitido.",
    "string_too_short": "Texto muito curto.",
    "string_too_long": "Texto muito longo.",
    "greater_than": "Deve ser maior que {gt}.",
    "greater_than_equal": "Deve ser maior ou igual a {ge}.",
    "less_than_equal": "Deve ser menor ou igual a {le}.",
    "less_than": "Deve ser menor que {lt}.",
    "decimal_max_places": "Use no máximo {decimal_places} casas decimais.",
    "decimal_max_digits": "Valor muito grande.",
    "decimal_parsing": "Valor numérico inválido.",
    "int_parsing": "Número inteiro inválido.",
    "int_from_float": "Deve ser um número inteiro.",
    "date_from_datetime_parsing": "Data inválida (use AAAA-MM-DD).",
    "date_parsing": "Data inválida (use AAAA-MM-DD).",
    "enum": "Valor inválido. Opções: {expected}.",
    "literal_error": "Valor inválido. Opções: {expected}.",
    "value_error": "{msg}",
    "bool_parsing": "Valor booleano inválido.",
}


def _translate(err: dict[str, Any]) -> str:
    template = _PYDANTIC_MESSAGES.get(err.get("type", ""))
    if template is None:
        return str(err.get("msg", "Valor inválido."))
    ctx = dict(err.get("ctx") or {})
    if err.get("type") == "value_error":
        msg = str(ctx.get("error", err.get("msg", "")))
        if "email address" in msg:
            return "E-mail inválido."
        return msg.removeprefix("Value error, ")
    try:
        return template.format(**ctx)
    except (KeyError, IndexError):
        return str(err.get("msg", "Valor inválido."))


def _field_name(loc: tuple[Any, ...]) -> str:
    parts = [str(p) for p in loc if p not in ("body", "query", "path")]
    return ".".join(parts) or "body"


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=error_body(exc.code, exc.message, exc.details))

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [{"field": _field_name(tuple(e.get("loc", ()))), "message": _translate(e)}
                   for e in exc.errors()]
        return JSONResponse(status_code=422, content=error_body("VALIDATION_ERROR", "Dados inválidos.", details))

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        codes = {400: "BAD_REQUEST", 401: "UNAUTHENTICATED", 403: "FORBIDDEN", 404: "NOT_FOUND",
                 405: "METHOD_NOT_ALLOWED", 409: "CONFLICT"}
        messages = {404: "Recurso não encontrado.", 405: "Método não permitido.", 401: "Autenticação necessária."}
        return JSONResponse(status_code=exc.status_code,
                            content=error_body(codes.get(exc.status_code, "ERROR"),
                                               messages.get(exc.status_code, str(exc.detail))),
                            headers=getattr(exc, "headers", None))

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
        import logging

        logging.getLogger("app").exception("Erro inesperado", exc_info=exc)
        return JSONResponse(status_code=500, content=error_body("INTERNAL_ERROR", "Erro interno do servidor."))
