"""API routes."""
from fastapi import APIRouter
from .routes import router as test_router
from .upload import router as upload_router

router = APIRouter()
router.include_router(test_router)
router.include_router(upload_router)
