from fastapi import APIRouter
from app.api.usuarios import router as usuarios_router
from app.api.productos import (
    router as productos_router,
    router_categorias,
    router_laboratorios,
    router_lotes,
    router_presentaciones,
)

router = APIRouter(prefix="/api/v1")
router.include_router(usuarios_router)
router.include_router(productos_router)
router.include_router(router_categorias)
router.include_router(router_laboratorios)
router.include_router(router_lotes)
router.include_router(router_presentaciones)
