from fastapi import APIRouter
from app.api.usuarios import router as usuarios_router
from app.api.autenticacion import router as autenticacion_router
from app.api.pedidos import router as pedidos_router

router = APIRouter(prefix="/api/v1")
router.include_router(usuarios_router)
router.include_router(autenticacion_router)
router.include_router(pedidos_router)