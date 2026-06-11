# ─────────────────────────────────────────────────────────────────────────────
# CAPA: SERVICE – Módulo de Facturas
# Responsabilidad: Generación, consulta y reemisión de facturas electrónicas.
# ─────────────────────────────────────────────────────────────────────────────

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi import HTTPException
import importlib.util, os, uuid, logging

logger = logging.getLogger(__name__)

# Cargar repositorio de facturas
_path_fac = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "repositories", "facturas", "facturas.repositori.py"))
_spec_fac = importlib.util.spec_from_file_location("facturas_repositori", _path_fac)
_mod_fac  = importlib.util.module_from_spec(_spec_fac)
_spec_fac.loader.exec_module(_mod_fac)
FacturaRepositorio = _mod_fac.FacturaRepositorio

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
PedidoRepositorio    = _mod_ped.PedidoRepositorio
ItemPedidoRepositorio = _mod_ped.ItemPedidoRepositorio

# Cargar repositorio de usuarios
_path_usr = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "repositories", "usuarios", "usuarios.repositori.py"))
_spec_usr = importlib.util.spec_from_file_location("usuarios_repositori", _path_usr)
_mod_usr  = importlib.util.module_from_spec(_spec_usr)
_spec_usr.loader.exec_module(_mod_usr)
UsuarioRepositorio = _mod_usr.UsuarioRepositorio

# Cargar repositorio de productos
_path_prod = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "repositories", "productos", "productos.respositori.py"))
_spec_prod = importlib.util.spec_from_file_location("productos_repositori", _path_prod)
_mod_prod  = importlib.util.module_from_spec(_spec_prod)
_spec_prod.loader.exec_module(_mod_prod)
ProductoRepositorio = _mod_prod.ProductoRepositorio

# Cargar adaptador de Factus
_path_fct = os.path.abspath(os.path.join(os.path.dirname(__file__), "factus.adapter.py"))
_spec_fct = importlib.util.spec_from_file_location("factus_adapter", _path_fct)
_mod_fct  = importlib.util.module_from_spec(_spec_fct)
_spec_fct.loader.exec_module(_mod_fct)
FactusAdapter = _mod_fct.FactusAdapter

from app.domain.pagos import Factura

ESTADOS_REEMITIBLES = ("error", "pendiente")


class FacturaService:
    def __init__(self, db: Session):
        self.db = db
        self.factura_repo = FacturaRepositorio(db)
        self.pago_repo    = PagoRepositorio(db)
        self.pedido_repo  = PedidoRepositorio(db)
        self.item_repo    = ItemPedidoRepositorio(db)
        self.usuario_repo = UsuarioRepositorio(db)
        self.producto_repo = ProductoRepositorio(db)
        self.factus       = FactusAdapter()

    def _siguiente_numero_factura(self) -> str:
        ahora = datetime.now(timezone.utc)
        ultimo = self.factura_repo.obtener_ultimo_numero()
        if ultimo and ultimo.startswith(f"FAC-{ahora.year}-"):
            consecutivo = int(ultimo.split("-")[-1]) + 1
        else:
            consecutivo = 1
        return f"FAC-{ahora.year}-{consecutivo:05d}"

    def generar_factura(self, pago_id, validar_aprobado: bool = True) -> dict:
        ahora = datetime.now(timezone.utc)

        pago = self.pago_repo.buscar_por_id(pago_id)
        if not pago:
            raise HTTPException(status_code=404, detail={
                "success": False, "statusCode": 404,
                "message": "Pago no encontrado",
                "error": {"error_code": "PAYMENT_NOT_FOUND",
                          "details": "No existe un pago con el ID proporcionado.",
                          "timestamp": ahora.isoformat()}
            })

        if validar_aprobado and pago.estado_transaccion != "APPROVED":
            raise HTTPException(status_code=409, detail={
                "success": False, "statusCode": 409,
                "message": "No se puede generar factura para este pago",
                "error": {"error_code": "PAYMENT_NOT_APPROVED",
                          "details": f"Solo se pueden generar facturas para pagos con estado APPROVED. El pago {pago_id} tiene estado {pago.estado_transaccion}.",
                          "timestamp": ahora.isoformat()}
            })

        factura_existente = self.factura_repo.buscar_por_pago_id(pago.id)
        if factura_existente:
            raise HTTPException(status_code=409, detail={
                "success": False, "statusCode": 409,
                "message": "Ya existe una factura para este pago",
                "error": {"error_code": "INVOICE_ALREADY_EXISTS",
                          "details": f"El pago {pago_id} ya tiene una factura generada con número {factura_existente.numero_factura}.",
                          "timestamp": ahora.isoformat()}
            })

        pedido = self.pedido_repo.buscar_por_id(pago.pedido_id)
        usuario = self.usuario_repo.buscar_por_id(pago.usuario_id)
        items_pedido = self.item_repo.buscar_por_pedido_id(pedido.id)

        numero_factura = self._siguiente_numero_factura()

        factura = Factura(
            id=uuid.uuid4(),
            pago_id=pago.id,
            pedido_id=pedido.id,
            usuario_id=usuario.id,
            numero_factura=numero_factura,
            subtotal_base=pedido.subtotal_base,
            total_iva=pedido.total_iva,
            total=pedido.total,
            estado_dian="pendiente",
            fecha_emision=ahora,
        )
        factura = self.factura_repo.guardar(factura)

        self._emitir_ante_factus(factura, pedido, items_pedido, usuario)

        return self._serializar_factura(factura, "Factura generada correctamente", 201)

    def _emitir_ante_factus(self, factura: Factura, pedido, items_pedido: list, usuario) -> None:
        productos_por_id = {
            item.producto_id: self.producto_repo.buscar_por_id(item.producto_id)
            for item in items_pedido
        }
        try:
            resultado = self.factus.emitir(factura.numero_factura, factura, pedido, items_pedido, usuario, productos_por_id)
            self.factura_repo.actualizar_emision(
                factura,
                cufe=resultado.get("cufe"),
                factus_id=resultado.get("factus_id"),
                url_pdf=resultado.get("url_pdf"),
                url_xml=resultado.get("url_xml"),
                estado_dian="emitida",
            )
        except Exception:
            logger.exception("Fallo al emitir la factura %s ante Factus", factura.numero_factura)
            self.factura_repo.actualizar_estado_dian(factura, "error")

    def consultar_por_id(self, factura_id, usuario_id, rol: str) -> dict:
        ahora = datetime.now(timezone.utc)
        factura = self.factura_repo.buscar_por_id(factura_id)
        if not factura:
            raise HTTPException(status_code=404, detail={
                "success": False, "statusCode": 404,
                "message": "Factura no encontrada",
                "error": {"error_code": "INVOICE_NOT_FOUND",
                          "details": "No existe una factura con el ID proporcionado.",
                          "timestamp": ahora.isoformat()}
            })

        if rol != "administrador" and str(factura.usuario_id) != str(usuario_id):
            raise HTTPException(status_code=403, detail={
                "success": False, "statusCode": 403,
                "message": "Acceso denegado",
                "error": {"error_code": "FORBIDDEN",
                          "details": "No tiene permisos para consultar esta factura.",
                          "timestamp": ahora.isoformat()}
            })

        return self._serializar_factura(factura, "Factura encontrada", 200)

    def reemitir_factura(self, factura_id) -> dict:
        ahora = datetime.now(timezone.utc)
        factura = self.factura_repo.buscar_por_id(factura_id)
        if not factura:
            raise HTTPException(status_code=404, detail={
                "success": False, "statusCode": 404,
                "message": "Factura no encontrada",
                "error": {"error_code": "INVOICE_NOT_FOUND",
                          "details": "No existe una factura con el ID proporcionado.",
                          "timestamp": ahora.isoformat()}
            })

        if factura.estado_dian not in ESTADOS_REEMITIBLES:
            raise HTTPException(status_code=409, detail={
                "success": False, "statusCode": 409,
                "message": "La factura no puede reemitirse en su estado actual",
                "error": {"error_code": "INVOICE_NOT_REISSUABLE",
                          "details": f"Solo se pueden reemitir facturas con estado_dian 'error' o 'pendiente'. La factura {factura_id} está en estado '{factura.estado_dian}'.",
                          "timestamp": ahora.isoformat()}
            })

        pedido = self.pedido_repo.buscar_por_id(factura.pedido_id)
        usuario = self.usuario_repo.buscar_por_id(factura.usuario_id)
        items_pedido = self.item_repo.buscar_por_pedido_id(pedido.id)

        self._emitir_ante_factus(factura, pedido, items_pedido, usuario)

        return self._serializar_factura(factura, "Factura reemitida correctamente", 200)

    def _serializar_factura(self, factura: Factura, mensaje: str, status_code: int) -> dict:
        return {
            "success": True,
            "statusCode": status_code,
            "message": mensaje,
            "data": {
                "facturaId": str(factura.id),
                "numeroFactura": factura.numero_factura,
                "pagoId": str(factura.pago_id),
                "pedidoId": str(factura.pedido_id),
                "usuarioId": str(factura.usuario_id),
                "subtotalBase": float(factura.subtotal_base),
                "totalIva": float(factura.total_iva),
                "total": float(factura.total),
                "cufe": factura.cufe,
                "factusId": factura.factus_id,
                "urlPdf": factura.url_pdf,
                "urlXml": factura.url_xml,
                "estadoDian": factura.estado_dian,
                "fechaEmision": factura.fecha_emision.isoformat(),
            }
        }
