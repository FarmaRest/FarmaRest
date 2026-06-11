# ─────────────────────────────────────────────────────────────────────────────
# CAPA: API – Módulo de Facturas
# Responsabilidad: Endpoints HTTP del módulo de facturas electrónicas.
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
_path_sch = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "domain", "facturas", "facturas.schemas.py"))
_spec_sch = importlib.util.spec_from_file_location("facturas_schemas", _path_sch)
_mod_sch  = importlib.util.module_from_spec(_spec_sch)
_spec_sch.loader.exec_module(_mod_sch)
FacturaEntrada = _mod_sch.FacturaEntrada

# Cargar servicio
_path_svc = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "services", "facturas", "facturas.services.py"))
_spec_svc = importlib.util.spec_from_file_location("facturas_services", _path_svc)
_mod_svc  = importlib.util.module_from_spec(_spec_svc)
_spec_svc.loader.exec_module(_mod_svc)
FacturaService = _mod_svc.FacturaService

router = APIRouter(prefix="/facturas", tags=["Facturas"])


def _requerir_administrador(usuario_actual):
    if usuario_actual.rol != "administrador":
        raise HTTPException(status_code=403, detail={
            "success": False, "statusCode": 403,
            "message": "Acceso denegado",
            "error": {"error_code": "FORBIDDEN",
                      "details": "Solo un administrador puede acceder a este recurso."}
        })


@router.post("", status_code=201)
def generar_factura(
    body: FacturaEntrada,
    db: Session = Depends(get_db),
    usuario_actual = Depends(get_usuario_actual)
):
    _requerir_administrador(usuario_actual)
    servicio = FacturaService(db)
    return servicio.generar_factura(pago_id=body.pagoId)


@router.get("/{factura_id}")
def consultar_factura_por_id(
    factura_id: UUID,
    db: Session = Depends(get_db),
    usuario_actual = Depends(get_usuario_actual)
):
    servicio = FacturaService(db)
    return servicio.consultar_por_id(
        factura_id=factura_id,
        usuario_id=usuario_actual.id,
        rol=usuario_actual.rol,
    )


@router.post("/{factura_id}/reemitir")
def reemitir_factura(
    factura_id: UUID,
    db: Session = Depends(get_db),
    usuario_actual = Depends(get_usuario_actual)
):
    _requerir_administrador(usuario_actual)
    servicio = FacturaService(db)
    return servicio.reemitir_factura(factura_id=factura_id)
