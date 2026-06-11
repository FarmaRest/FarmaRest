# ─────────────────────────────────────────────────────────────────────────────
# CAPA: SERVICE – Módulo de Envíos
# Responsabilidad: Registro de envíos para pedidos pagados, calculando el costo
# de envío según las reglas de negocio de la droguería.
# ─────────────────────────────────────────────────────────────────────────────

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi import HTTPException
import importlib.util, os, uuid

# Cargar repositorio de envíos
_path_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "repositories", "envios", "envios.repositori.py"))
_spec_env = importlib.util.spec_from_file_location("envios_repositori", _path_env)
_mod_env  = importlib.util.module_from_spec(_spec_env)
_spec_env.loader.exec_module(_mod_env)
EnvioRepositorio = _mod_env.EnvioRepositorio

# Cargar repositorio de pedidos
_path_ped = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "repositories", "pedidos", "pedidos.repositori.py"))
_spec_ped = importlib.util.spec_from_file_location("pedidos_repositori", _path_ped)
_mod_ped  = importlib.util.module_from_spec(_spec_ped)
_spec_ped.loader.exec_module(_mod_ped)
PedidoRepositorio = _mod_ped.PedidoRepositorio

from app.domain.envios import Envio

UMBRAL_ENVIO_GRATIS = 120000  # >= este total, el envío es gratuito
UMBRAL_COSTO_FIJO   = 20000   # < este total, no aplica esta tabla de costos

# Tarifas fijas de envío por ciudad, definidas por la droguería.
# Aplican para pedidos con total entre $20.000 y $119.999 COP.
TARIFAS_ENVIO_POR_CIUDAD = {
    "bogota":       12000,
    "bogotá":       12000,
    "medellin":     15000,
    "medellín":     15000,
    "cali":         15000,
    "barranquilla": 18000,
    "bucaramanga":  14000,
}
TARIFA_ENVIO_DEFECTO = 15000


class EnvioService:
    def __init__(self, db: Session):
        self.db = db
        self.envio_repo  = EnvioRepositorio(db)
        self.pedido_repo = PedidoRepositorio(db)

    def _calcular_costo_envio(self, total: float, ciudad: str) -> float:
        if total >= UMBRAL_ENVIO_GRATIS:
            return 0
        if total >= UMBRAL_COSTO_FIJO:
            return TARIFAS_ENVIO_POR_CIUDAD.get(ciudad.strip().lower(), TARIFA_ENVIO_DEFECTO)
        return TARIFA_ENVIO_DEFECTO

    def registrar_envio(self, pedido_id, usuario_id, direccion: str, ciudad: str, empresa_transporte: str, fecha_despacho) -> dict:
        ahora = datetime.now(timezone.utc)

        pedido = self.pedido_repo.buscar_por_id(pedido_id)
        if not pedido:
            raise HTTPException(status_code=404, detail={
                "success": False, "statusCode": 404,
                "message": "Pedido no encontrado",
                "error": {"error_code": "ORDER_NOT_FOUND",
                          "details": "No existe un pedido con el ID proporcionado.",
                          "timestamp": ahora.isoformat()}
            })

        if pedido.estado != "pagado":
            raise HTTPException(status_code=409, detail={
                "success": False, "statusCode": 409,
                "message": "El pedido no está disponible para despacho",
                "error": {"error_code": "ORDER_NOT_PAID",
                          "details": f"Solo se pueden generar envíos para pedidos en estado 'pagado'. El pedido {pedido_id} está en estado '{pedido.estado}'.",
                          "timestamp": ahora.isoformat()}
            })

        envio_existente = self.envio_repo.buscar_por_pedido_id(pedido_id)
        if envio_existente:
            raise HTTPException(status_code=409, detail={
                "success": False, "statusCode": 409,
                "message": "Ya existe un envío registrado para este pedido",
                "error": {"error_code": "SHIPMENT_ALREADY_EXISTS",
                          "details": f"El pedido {pedido_id} ya tiene un envío registrado con ID {envio_existente.id}.",
                          "timestamp": ahora.isoformat()}
            })

        costo_envio = self._calcular_costo_envio(float(pedido.total), ciudad)

        envio = Envio(
            id=uuid.uuid4(),
            pedido_id=pedido.id,
            usuario_id=usuario_id,
            estado="en_preparacion",
            direccion_entrega=direccion,
            ciudad_entrega=ciudad,
            empresa_transporte=empresa_transporte,
            fecha_despacho=fecha_despacho,
            costo_envio=costo_envio,
            fecha_creacion=ahora,
            fecha_actualizacion=ahora,
        )
        envio = self.envio_repo.guardar(envio)

        return self._serializar_envio(envio, "Envío registrado correctamente", 201)

    def listar_envios(self) -> dict:
        envios = self.envio_repo.listar_todos()
        return {
            "success": True,
            "statusCode": 200,
            "message": "Envíos obtenidos correctamente",
            "data": [
                {
                    "envioId": str(envio.id),
                    "pedidoId": str(envio.pedido_id),
                    "estado": envio.estado,
                    "empresaTransporte": envio.empresa_transporte,
                    "fechaDespacho": envio.fecha_despacho.isoformat(),
                }
                for envio in envios
            ]
        }

    def consultar_por_id(self, envio_id, usuario_id, rol) -> dict:
        ahora = datetime.now(timezone.utc)

        envio = self.envio_repo.buscar_por_id(envio_id)
        if not envio:
            raise HTTPException(status_code=404, detail={
                "success": False, "statusCode": 404,
                "message": "Envío no encontrado",
                "error": {"error_code": "SHIPMENT_NOT_FOUND",
                          "details": "No existe un envío con el ID o pedido proporcionado.",
                          "timestamp": ahora.isoformat()}
            })

        self._verificar_permiso(envio, usuario_id, rol, ahora)

        return self._serializar_envio(envio, "Envío encontrado", 200)

    def consultar_por_pedido_id(self, pedido_id, usuario_id, rol) -> dict:
        ahora = datetime.now(timezone.utc)

        envio = self.envio_repo.buscar_por_pedido_id(pedido_id)
        if not envio:
            raise HTTPException(status_code=404, detail={
                "success": False, "statusCode": 404,
                "message": "Envío no encontrado",
                "error": {"error_code": "SHIPMENT_NOT_FOUND",
                          "details": "No existe un envío con el ID o pedido proporcionado.",
                          "timestamp": ahora.isoformat()}
            })

        self._verificar_permiso(envio, usuario_id, rol, ahora)

        return self._serializar_envio(envio, "Envío encontrado", 200)

    def _verificar_permiso(self, envio: Envio, usuario_id, rol, ahora) -> None:
        if rol != "administrador" and envio.usuario_id != usuario_id:
            raise HTTPException(status_code=403, detail={
                "success": False, "statusCode": 403,
                "message": "Acceso denegado",
                "error": {"error_code": "FORBIDDEN",
                          "details": "No tiene permisos para consultar este envío.",
                          "timestamp": ahora.isoformat()}
            })

    def _serializar_envio(self, envio: Envio, mensaje: str, status_code: int) -> dict:
        return {
            "success": True,
            "statusCode": status_code,
            "message": mensaje,
            "data": {
                "envioId": str(envio.id),
                "pedidoId": str(envio.pedido_id),
                "estado": envio.estado,
                "direccionEntrega": {
                    "direccion": envio.direccion_entrega,
                    "ciudad": envio.ciudad_entrega,
                },
                "empresaTransporte": envio.empresa_transporte,
                "fechaDespacho": envio.fecha_despacho.isoformat(),
                "costoEnvio": float(envio.costo_envio),
            }
        }
