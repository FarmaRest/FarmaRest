from sqlalchemy.orm import Session
from datetime import datetime, timezone, time
from zoneinfo import ZoneInfo
from fastapi import HTTPException
import importlib.util, os, uuid

# Cargar repositorio de pagos
_path_pag = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "repositories", "pagos", "pagos.repositori.py"))
_spec_pag = importlib.util.spec_from_file_location("pagos_repositori", _path_pag)
_mod_pag  = importlib.util.module_from_spec(_spec_pag)
_spec_pag.loader.exec_module(_mod_pag)
PagoRepositorio = _mod_pag.PagoRepositorio

# Cargar repositorio de pedidos
_path_ped = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "repositories", "pedidos", "pedidos.repositori.py"))
_spec_ped = importlib.util.spec_from_file_location("pedidos_repositori", _path_ped)
_mod_ped  = importlib.util.module_from_spec(_spec_ped)
_spec_ped.loader.exec_module(_mod_ped)
PedidoRepositorio = _mod_ped.PedidoRepositorio

# Cargar adaptador de Wompi
_path_wmp = os.path.abspath(os.path.join(os.path.dirname(__file__), "wompi.adapter.py"))
_spec_wmp = importlib.util.spec_from_file_location("wompi_adapter", _path_wmp)
_mod_wmp  = importlib.util.module_from_spec(_spec_wmp)
_spec_wmp.loader.exec_module(_mod_wmp)
WompiAdapter = _mod_wmp.WompiAdapter

from app.domain.pagos import Pago

HORA_INICIO_PERMITIDA = time(6, 0)   # 6:00 AM
HORA_FIN_PERMITIDA    = time(23, 0)  # 11:00 PM
ZONA_COLOMBIA         = ZoneInfo("America/Bogota")


class PagoService:
    def __init__(self, db: Session):
        self.db = db
        self.pago_repo   = PagoRepositorio(db)
        self.pedido_repo = PedidoRepositorio(db)
        self.wompi       = WompiAdapter()

    def _validar_horario_permitido(self, ahora: datetime):
        hora_actual = ahora.astimezone(ZONA_COLOMBIA).time()
        if not (HORA_INICIO_PERMITIDA <= hora_actual <= HORA_FIN_PERMITIDA):
            raise HTTPException(status_code=403, detail={
                "success": False, "statusCode": 403,
                "message": "El servicio de pagos no está disponible en este momento",
                "error": {"error_code": "PAYMENT_OUTSIDE_ALLOWED_HOURS",
                          "details": "Las transacciones solo se procesan entre las 6:00 AM y las 11:00 PM.",
                          "timestamp": ahora.isoformat()}
            })

    def iniciar_pago(self, usuario_id, pedido_id, monto_en_centavos: int, moneda: str, correo_cliente: str) -> dict:
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

        if str(pedido.usuario_id) != str(usuario_id):
            raise HTTPException(status_code=403, detail={
                "success": False, "statusCode": 403,
                "message": "Acceso denegado",
                "error": {"error_code": "FORBIDDEN",
                          "details": "El pedido indicado no pertenece al usuario autenticado.",
                          "timestamp": ahora.isoformat()}
            })

        if pedido.estado != "pendiente":
            raise HTTPException(status_code=409, detail={
                "success": False, "statusCode": 409,
                "message": "El pedido no está disponible para pago",
                "error": {"error_code": "ORDER_NOT_PAYABLE",
                          "details": f"Solo se pueden pagar pedidos en estado 'pendiente'. El pedido {pedido_id} está en estado '{pedido.estado}'.",
                          "timestamp": ahora.isoformat()}
            })

        monto_esperado = round(float(pedido.total) * 100)
        if monto_en_centavos != monto_esperado:
            raise HTTPException(status_code=400, detail={
                "success": False, "statusCode": 400,
                "message": "El monto enviado no coincide con el total del pedido",
                "error": {"error_code": "AMOUNT_MISMATCH",
                          "details": f"El montoEnCentavos debe ser {monto_esperado} (total del pedido x 100). Se recibió {monto_en_centavos}.",
                          "timestamp": ahora.isoformat()}
            })

        self._validar_horario_permitido(ahora)

        timestamp = int(ahora.timestamp())
        referencia_interna = f"FARMA-PED-{pedido.id}-{timestamp}"

        respuesta_wompi = self.wompi.crear_transaccion(
            monto_en_centavos=monto_en_centavos,
            moneda=moneda,
            referencia=referencia_interna,
            correo_cliente=correo_cliente,
        )

        pago = Pago(
            id=uuid.uuid4(),
            pedido_id=pedido.id,
            usuario_id=usuario_id,
            referencia_interna=referencia_interna,
            monto_en_centavos=monto_en_centavos,
            moneda=moneda,
            estado_transaccion=respuesta_wompi["estado"],
            url_checkout=respuesta_wompi["urlCheckout"],
            fecha_creacion=ahora,
            fecha_actualizacion=ahora,
        )
        self.pago_repo.guardar(pago)
        self.db.commit()
        self.db.refresh(pago)

        return {
            "success": True,
            "statusCode": 201,
            "message": "Transacción iniciada correctamente, redirigir al cliente al checkout de pago.",
            "data": {
                "pagoId": str(pago.id),
                "urlCheckout": pago.url_checkout,
                "referenciaInterna": pago.referencia_interna,
                "estadoTransaccion": pago.estado_transaccion,
            }
        }

    def consultar_por_id(self, pago_id, usuario_id, rol: str) -> dict:
        ahora = datetime.now(timezone.utc)
        pago = self.pago_repo.buscar_por_id(pago_id)
        if not pago:
            raise HTTPException(status_code=404, detail={
                "success": False, "statusCode": 404,
                "message": "Pago no encontrado",
                "error": {"error_code": "PAYMENT_NOT_FOUND",
                          "details": "No existe un pago con el ID o referencia proporcionada.",
                          "timestamp": ahora.isoformat()}
            })

        if rol != "administrador" and str(pago.usuario_id) != str(usuario_id):
            raise HTTPException(status_code=403, detail={
                "success": False, "statusCode": 403,
                "message": "Acceso denegado",
                "error": {"error_code": "FORBIDDEN",
                          "details": "No tiene permisos para consultar este pago.",
                          "timestamp": ahora.isoformat()}
            })

        return self._serializar_pago(pago, "Pago encontrado")

    def consultar_por_referencia(self, referencia_interna: str) -> dict:
        ahora = datetime.now(timezone.utc)
        pago = self.pago_repo.buscar_por_referencia(referencia_interna)
        if not pago:
            raise HTTPException(status_code=404, detail={
                "success": False, "statusCode": 404,
                "message": "Pago no encontrado",
                "error": {"error_code": "PAYMENT_NOT_FOUND",
                          "details": "No existe un pago con el ID o referencia proporcionada.",
                          "timestamp": ahora.isoformat()}
            })

        return self._serializar_pago(pago, "Pago encontrado")

    def _serializar_pago(self, pago: Pago, mensaje: str) -> dict:
        return {
            "success": True,
            "statusCode": 200,
            "message": mensaje,
            "data": {
                "pagoId": str(pago.id),
                "pedidoId": str(pago.pedido_id),
                "referenciaInterna": pago.referencia_interna,
                "idTransaccionWompi": pago.id_transaccion_wompi,
                "montoEnCentavos": pago.monto_en_centavos,
                "moneda": pago.moneda,
                "metodoPago": pago.metodo_pago,
                "estadoTransaccion": pago.estado_transaccion,
                "fechaPago": pago.fecha_actualizacion.isoformat(),
            }
        }
