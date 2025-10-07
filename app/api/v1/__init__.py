from fastapi import APIRouter

from app.api.v1 import company

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(company.router, prefix="/companies", tags=["companies"])
