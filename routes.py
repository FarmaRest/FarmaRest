from fastapi import APIRouter
from app.api.usuarios import router as usuarios_router
from app.api.autenticacion import router as autenticacion_router
from app.api.productos import (
    router as productos_router,
    router_categorias,
    router_laboratorios,
    router_lotes,
    router_presentaciones,
)
from app.api.carritos import router as carritos_router
from app.api.pedidos import router as pedidos_router
from app.api.pagos import router as pagos_router
from app.api.facturas import router as facturas_router

router = APIRouter(prefix="/api/v1")
router.include_router(usuarios_router)
router.include_router(autenticacion_router)
router.include_router(productos_router)
router.include_router(router_categorias)
router.include_router(router_laboratorios)
router.include_router(router_lotes)
router.include_router(router_presentaciones)
router.include_router(carritos_router)
router.include_router(pedidos_router)
router.include_router(pagos_router)
router.include_router(facturas_router)
