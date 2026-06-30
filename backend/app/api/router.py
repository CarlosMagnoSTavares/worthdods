from fastapi import APIRouter
from app.api import properties, analysis, legal, favorites, admin, auth, cost_calculator, url_verification

api_router = APIRouter()

api_router.include_router(properties.router)
api_router.include_router(analysis.router)
api_router.include_router(legal.router)
api_router.include_router(favorites.router)
api_router.include_router(admin.router)
api_router.include_router(auth.router)
api_router.include_router(cost_calculator.router)
api_router.include_router(url_verification.router)
