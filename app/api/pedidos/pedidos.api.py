# ─────────────────────────────────────────────────────────────────────────────
# CAPA: API – Módulo de Pedidos
# Responsabilidad: Endpoints HTTP del módulo de pedidos.
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import importlib.util, os

from app.core.database import get_db

# Cargar dependencia de autenticación
_path_auth = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "autenticacion", "autenticacion.api.py"))
_spec_auth = importlib.util.spec_from_file_location("autenticacion_api", _path_auth)
_mod_auth  = importlib.util.module_from_spec(_spec_auth)
_spec_auth.loader.exec_module(_mod_auth)
get_usuario_actual = _mod_auth.get_usuario_actual

# Cargar schemas
_path_sch = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "domain", "pedidos", "pedidos.schemas.py"))
_spec_sch = importlib.util.spec_from_file_location("pedidos_schemas", _path_sch)
_mod_sch  = importlib.util.module_from_spec(_spec_sch)
_spec_sch.loader.exec_module(_mod_sch)
PedidoEntrada = _mod_sch.PedidoEntrada

# Cargar servicio
_path_svc = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "services", "pedidos", "pedidos.services.py"))
_spec_svc = importlib.util.spec_from_file_location("pedidos_services", _path_svc)
_mod_svc  = importlib.util.module_from_spec(_spec_svc)
_spec_svc.loader.exec_module(_mod_svc)
PedidoService = _mod_svc.PedidoService

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


@router.post("", status_code=201)
def crear_pedido(
    body: PedidoEntrada,
    db: Session = Depends(get_db),
    usuario_actual = Depends(get_usuario_actual)
):
    servicio = PedidoService(db)
    return servicio.crear_pedido(
        usuario_id=usuario_actual.id,
        carrito_id=body.carrito_id,
        direccion=body.direccion_entrega.direccion,
        ciudad=body.direccion_entrega.ciudad,
        metodo_pago=body.metodo_pago
    )