from fastapi import APIRouter

from app.routers.admin import router as admin_router
from app.routers.availability import router as availability_router
from app.routers.catalog import router as catalog_router
from app.routers.recommendations import router as recommendations_router
from app.routers.reservations import router as reservations_router
from app.routers.safi import router as safi_router


router = APIRouter()
router.include_router(catalog_router)
router.include_router(availability_router)
router.include_router(reservations_router)
router.include_router(recommendations_router)
router.include_router(safi_router)
router.include_router(admin_router)
