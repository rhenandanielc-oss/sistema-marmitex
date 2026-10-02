from fastapi import APIRouter

from app.api.v1.routes import audit, auth, health, registry, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(registry.companies)
api_router.include_router(registry.customers)
api_router.include_router(registry.categories)
api_router.include_router(audit.router)
