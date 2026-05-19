from fastapi import APIRouter
from app.api.usuarios import router as usuarios_router

router = APIRouter(prefix="/api/v1")
router.include_router(usuarios_router)
