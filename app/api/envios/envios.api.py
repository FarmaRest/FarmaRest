# ─────────────────────────────────────────────────────────────────────────────
# CAPA: API – Módulo de Envíos
# Responsabilidad: Endpoints HTTP del módulo de envíos.
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
import importlib.util, os

from app.core.database import get_db

# Cargar dependencia de autenticación
_path_auth = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "autenticacion", "autenticacion.api.py"))
_spec_auth = importlib.util.spec_from_file_location("autenticacion_api", _path_auth)
_mod_auth  = importlib.util.module_from_spec(_spec_auth)
_spec_auth.loader.exec_module(_mod_auth)
get_usuario_actual = _mod_auth.get_usuario_actual

# Cargar schemas
_path_sch = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "domain", "envios", "envios.schemas.py"))
_spec_sch = importlib.util.spec_from_file_location("envios_schemas", _path_sch)
_mod_sch  = importlib.util.module_from_spec(_spec_sch)
_spec_sch.loader.exec_module(_mod_sch)
EnvioEntrada = _mod_sch.EnvioEntrada
ActualizarEstadoEnvioEntrada = _mod_sch.ActualizarEstadoEnvioEntrada

# Cargar servicio
_path_svc = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "services", "envios", "envios.services.py"))
_spec_svc = importlib.util.spec_from_file_location("envios_services", _path_svc)
_mod_svc  = importlib.util.module_from_spec(_spec_svc)
_spec_svc.loader.exec_module(_mod_svc)
EnvioService = _mod_svc.EnvioService

router = APIRouter(prefix="/envios", tags=["Envíos"])


def _requerir_administrador(usuario_actual):
    if usuario_actual.rol != "administrador":
        raise HTTPException(status_code=403, detail={
            "success": False, "statusCode": 403,
            "message": "Acceso denegado",
            "error": {"error_code": "FORBIDDEN",
                      "details": "Solo un administrador puede acceder a este recurso."}
        })


@router.post("", status_code=201)
def registrar_envio(
    body: EnvioEntrada,
    db: Session = Depends(get_db),
    usuario_actual = Depends(get_usuario_actual)
):
    _requerir_administrador(usuario_actual)
    servicio = EnvioService(db)
    return servicio.registrar_envio(
        pedido_id=body.pedidoId,
        usuario_id=body.usuarioId,
        direccion=body.direccionEntrega.direccion,
        ciudad=body.direccionEntrega.ciudad,
        empresa_transporte=body.empresaTransporte,
        fecha_despacho=body.fechaDespacho,
    )


@router.get("")
def listar_envios(
    db: Session = Depends(get_db),
    usuario_actual = Depends(get_usuario_actual)
):
    _requerir_administrador(usuario_actual)
    servicio = EnvioService(db)
    return servicio.listar_envios()


@router.get("/pedido/{pedido_id}")
def consultar_envio_por_pedido(
    pedido_id: UUID,
    db: Session = Depends(get_db),
    usuario_actual = Depends(get_usuario_actual)
):
    servicio = EnvioService(db)
    return servicio.consultar_por_pedido_id(pedido_id, usuario_actual.id, usuario_actual.rol)


@router.get("/{envio_id}")
def consultar_envio_por_id(
    envio_id: UUID,
    db: Session = Depends(get_db),
    usuario_actual = Depends(get_usuario_actual)
):
    servicio = EnvioService(db)
    return servicio.consultar_por_id(envio_id, usuario_actual.id, usuario_actual.rol)


@router.patch("/{envio_id}")
def actualizar_estado_envio(
    envio_id: UUID,
    body: ActualizarEstadoEnvioEntrada,
    db: Session = Depends(get_db),
    usuario_actual = Depends(get_usuario_actual)
):
    _requerir_administrador(usuario_actual)
    servicio = EnvioService(db)
    return servicio.actualizar_estado_envio(envio_id, body.estado)
