from fastapi import APIRouter

from service.api.v1.healthcheck.router import router as healthcheck_router
from service.api.v1.leads.router import router as leads_router

v1_router = APIRouter(prefix='/api/v1', tags=['v1'])
v1_router.include_router(healthcheck_router)
v1_router.include_router(leads_router)
