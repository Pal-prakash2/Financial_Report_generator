from fastapi import APIRouter

from app.api.v1 import company
from app.api.v1.endpoints import files_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(company.router, prefix="/companies", tags=["companies"])
api_router.include_router(files_router, prefix="/files", tags=["files"])
