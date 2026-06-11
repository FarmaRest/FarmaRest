# ─────────────────────────────────────────────────────────────────────────────
# CAPA: API – Módulo de Pagos
# Responsabilidad: Endpoints HTTP del módulo de pagos.
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import importlib.util, os
from uuid import UUID

from app.core.database import get_db

# Cargar dependencia de autenticación
_path_auth = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "autenticacion", "autenticacion.api.py"))
_spec_auth = importlib.util.spec_from_file_location("autenticacion_api", _path_auth)
_mod_auth  = importlib.util.module_from_spec(_spec_auth)
_spec_auth.loader.exec_module(_mod_auth)
get_usuario_actual = _mod_auth.get_usuario_actual

# Cargar schemas
_path_sch = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "domain", "pagos", "pagos.schemas.py"))
_spec_sch = importlib.util.spec_from_file_location("pagos_schemas", _path_sch)
_mod_sch  = importlib.util.module_from_spec(_spec_sch)
_spec_sch.loader.exec_module(_mod_sch)
PagoEntrada = _mod_sch.PagoEntrada

# Cargar servicio
_path_svc = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "services", "pagos", "pagos.services.py"))
_spec_svc = importlib.util.spec_from_file_location("pagos_services", _path_svc)
_mod_svc  = importlib.util.module_from_spec(_spec_svc)
_spec_svc.loader.exec_module(_mod_svc)
PagoService = _mod_svc.PagoService

router = APIRouter(prefix="/pagos", tags=["Pagos"])


@router.post("", status_code=201)
def iniciar_pago(
    body: PagoEntrada,
    db: Session = Depends(get_db),
    usuario_actual = Depends(get_usuario_actual)
):
    servicio = PagoService(db)
    return servicio.iniciar_pago(
        usuario_id=usuario_actual.id,
        pedido_id=body.pedidoId,
        monto_en_centavos=body.montoEnCentavos,
        moneda=body.moneda,
        correo_cliente=body.correoCliente,
    )


@router.get("/referencia/{referencia}")
def consultar_pago_por_referencia(
    referencia: str,
    db: Session = Depends(get_db),
    usuario_actual = Depends(get_usuario_actual)
):
    if usuario_actual.rol != "administrador":
        raise HTTPException(status_code=403, detail={
            "success": False, "statusCode": 403,
            "message": "Acceso denegado",
            "error": {"error_code": "FORBIDDEN",
                      "details": "Solo un administrador puede acceder a este recurso."}
        })
    servicio = PagoService(db)
    return servicio.consultar_por_referencia(referencia)


@router.get("/{pago_id}")
def consultar_pago_por_id(
    pago_id: UUID,
    db: Session = Depends(get_db),
    usuario_actual = Depends(get_usuario_actual)
):
    servicio = PagoService(db)
    return servicio.consultar_por_id(
        pago_id=pago_id,
        usuario_id=usuario_actual.id,
        rol=usuario_actual.rol,
    )
