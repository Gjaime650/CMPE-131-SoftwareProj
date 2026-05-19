from fastapi import APIRouter

from app.api.v1.endpoints.rapidapi import router as rapidapi_router
from app.api.v1.endpoints.flights import router as flights_router
from app.api.v1.endpoints.booking import router as booking_router


api_router = APIRouter()
api_router.include_router(rapidapi_router)
api_router.include_router(flights_router)
api_router.include_router(booking_router)
