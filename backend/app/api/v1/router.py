from fastapi import APIRouter

from app.api.v1.routes import audit, auth, entries, health, registry, reports, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(registry.companies)
api_router.include_router(registry.customers)
api_router.include_router(registry.categories)
api_router.include_router(entries.sales)
api_router.include_router(entries.costs)
api_router.include_router(reports.history_router)
api_router.include_router(reports.dashboard)
api_router.include_router(audit.router)
