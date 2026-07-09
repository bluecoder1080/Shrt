from fastapi import APIRouter
from app.api.v1 import auth, urls, analytics

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(urls.router, prefix="/urls", tags=["URLs"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
