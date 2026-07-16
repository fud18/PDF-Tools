"""Version 1 API route registration."""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.pdf.fill import router as fill_router
from app.api.v1.pdf.inspect import router as inspect_router

router = APIRouter(prefix="/v1")

router.include_router(health_router)
router.include_router(inspect_router, prefix="/pdf")
router.include_router(fill_router, prefix="/pdf")
