from fastapi import APIRouter
from app.api.usuarios import router as usuarios_router
from app.api.productos import router as productos_router

router = APIRouter(prefix="/api/v1")
router.include_router(usuarios_router)
router.include_router(productos_router)
