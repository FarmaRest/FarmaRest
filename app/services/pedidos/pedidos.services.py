from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi import HTTPException
import importlib.util, os, uuid

# Cargar repositorio de pedidos
_path_ped = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "repositories", "pedidos", "pedidos.repositori.py"))
_spec_ped = importlib.util.spec_from_file_location("pedidos_repositori", _path_ped)
_mod_ped  = importlib.util.module_from_spec(_spec_ped)
_spec_ped.loader.exec_module(_mod_ped)
PedidoRepositorio     = _mod_ped.PedidoRepositorio
ItemPedidoRepositorio = _mod_ped.ItemPedidoRepositorio

# Cargar repositorio de carritos
_path_car = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "repositories", "carritos", "carritos.repositori.py"))
_spec_car = importlib.util.spec_from_file_location("carritos_repositori", _path_car)
_mod_car  = importlib.util.module_from_spec(_spec_car)
_spec_car.loader.exec_module(_mod_car)
CarritoRepositorio     = _mod_car.CarritoRepositorio
ItemCarritoRepositorio = _mod_car.ItemCarritoRepositorio

# Cargar modelos usando import directo
from app.domain.pedidos import Pedido, ItemPedido

MONTO_MINIMO = 20000
ESTADOS_VALIDOS = ["pendiente", "pagado", "en_preparacion", "enviado", "entregado"]
FLUJO_ESTADOS = {
    "pendiente":      "pagado",
    "pagado":         "en_preparacion",
    "en_preparacion": "enviado",
    "enviado":        "entregado"
}
ESTADOS_NO_CANCELABLES = ["en_preparacion", "enviado", "entregado"]


class PedidoService:
    def __init__(self, db: Session):
        self.db = db
        self.pedido_repo       = PedidoRepositorio(db)
        self.item_pedido_repo  = ItemPedidoRepositorio(db)
        self.carrito_repo      = CarritoRepositorio(db)
        self.item_carrito_repo = ItemCarritoRepositorio(db)

    def crear_pedido(self, usuario_id, carrito_id, direccion: str, ciudad: str, metodo_pago: str) -> dict:
        ahora = datetime.now(timezone.utc)

        carrito = self.carrito_repo.buscar_por_id(carrito_id)
        if not carrito:
            raise HTTPException(status_code=404, detail={
                "success": False, "statusCode": 404,
                "message": "Carrito no encontrado",
                "error": {"error_code": "CART_NOT_FOUND", "timestamp": ahora.isoformat()}
            })
        if str(carrito.usuario_id) != str(usuario_id):
            raise HTTPException(status_code=403, detail={
                "success": False, "statusCode": 403,
                "message": "Acceso denegado",
                "error": {"error_code": "FORBIDDEN",
                          "details": "El carrito indicado no pertenece al usuario autenticado.",
                          "timestamp": ahora.isoformat()}
            })

        items_carrito = self.item_carrito_repo.buscar_por_carrito_id(carrito_id)

        if not items_carrito:
            raise HTTPException(status_code=400, detail={
                "success": False, "statusCode": 400,
                "message": "No se puede crear el pedido con el carrito vacío",
                "error": {"error_code": "EMPTY_CART",
                          "details": "El carrito del usuario no contiene productos",
                          "timestamp": ahora.isoformat()}
            })

        productos_distintos = len(set(str(item.producto_id) for item in items_carrito))
        if productos_distintos < 2:
            raise HTTPException(status_code=400, detail={
                "success": False, "statusCode": 400,
                "message": "El carrito no cumple el mínimo de productos requeridos para proceder al pago",
                "error": {"error_code": "MIN_PRODUCTS_NOT_MET",
                          "details": f"El carrito debe contener al menos 2 productos diferentes. Actualmente tienes {productos_distintos} producto diferente.",
                          "timestamp": ahora.isoformat()}
            })

        total = float(carrito.total)
        if total < MONTO_MINIMO:
            raise HTTPException(status_code=400, detail={
                "success": False, "statusCode": 400,
                "message": "El monto del pedido no alcanza el mínimo requerido",
                "error": {"error_code": "ORDER_BELOW_MINIMUM",
                          "details": f"El monto mínimo para crear un pedido es de $20.000 COP. Tu carrito tiene un total de ${int(total):,} COP.",
                          "timestamp": ahora.isoformat()}
            })

        pedido = Pedido(
            id=uuid.uuid4(),
            usuario_id=usuario_id,
            carrito_id=carrito_id,
            estado="pendiente",
            subtotal_base=carrito.subtotal_base,
            total_iva=carrito.total_iva,
            total=carrito.total,
            direccion_entrega=direccion,
            ciudad_entrega=ciudad,
            metodo_pago=metodo_pago,
            fecha_creacion=ahora,
            fecha_actualizacion=ahora
        )
        self.pedido_repo.guardar(pedido)

        items_pedido = []
        for item in items_carrito:
            item_pedido = ItemPedido(
                id=uuid.uuid4(),
                pedido_id=pedido.id,
                producto_id=item.producto_id,
                cantidad=item.cantidad,
                precio_unitario=item.precio_unitario,
                iva_unitario=item.iva_unitario,
                subtotal=item.subtotal
            )
            items_pedido.append(item_pedido)
        self.item_pedido_repo.guardar_todos(items_pedido)

        self.carrito_repo.desactivar(carrito_id)
        self.db.commit()
        self.db.refresh(pedido)

        return {
            "success": True,
            "statusCode": 201,
            "message": "Pedido creado correctamente",
            "data": {
                "pedidoId": str(pedido.id),
                "usuarioId": str(pedido.usuario_id),
                "estado": pedido.estado,
                "items": [
                    {
                        "productoId": str(i.producto_id),
                        "cantidad": i.cantidad,
                        "precioUnitario": float(i.precio_unitario),
                        "ivaUnitario": float(i.iva_unitario),
                        "subtotal": float(i.subtotal)
                    } for i in items_pedido
                ],
                "subtotalBase": float(pedido.subtotal_base),
                "totalIva": float(pedido.total_iva),
                "total": float(pedido.total),
                "fechaCreacion": pedido.fecha_creacion.isoformat()
            }
        }

    def listar_pedidos(self, usuario_id, rol: str) -> dict:
        if rol == "administrador":
            pedidos = self.pedido_repo.listar_todos()
        else:
            pedidos = self.pedido_repo.buscar_por_usuario_id(usuario_id)

        return {
            "success": True,
            "statusCode": 200,
            "message": "Pedidos obtenidos correctamente",
            "data": [
                {
                    "pedidoId": str(p.id),
                    "usuarioId": str(p.usuario_id),
                    "estado": p.estado,
                    "subtotalBase": float(p.subtotal_base),
                    "totalIva": float(p.total_iva),
                    "total": float(p.total),
                    "fechaCreacion": p.fecha_creacion.isoformat()
                } for p in pedidos
            ]
        }

    def consultar_por_id(self, pedido_id, usuario_id, rol: str) -> dict:
        ahora = datetime.now(timezone.utc)
        pedido = self.pedido_repo.buscar_por_id(pedido_id)
        if not pedido:
            raise HTTPException(status_code=404, detail={
                "success": False, "statusCode": 404,
                "message": "Pedido no encontrado",
                "error": {"error_code": "ORDER_NOT_FOUND",
                          "details": "No existe un pedido con el ID proporcionado",
                          "timestamp": ahora.isoformat()}
            })
        if rol != "administrador" and str(pedido.usuario_id) != str(usuario_id):
            raise HTTPException(status_code=403, detail={
                "success": False, "statusCode": 403,
                "message": "Acceso denegado",
                "error": {"error_code": "FORBIDDEN",
                          "details": "No tiene permisos para consultar este pedido.",
                          "timestamp": ahora.isoformat()}
            })

        items = self.item_pedido_repo.buscar_por_pedido_id(pedido_id)

        return {
            "success": True,
            "statusCode": 200,
            "message": "Pedido encontrado",
            "data": {
                "pedidoId": str(pedido.id),
                "usuarioId": str(pedido.usuario_id),
                "estado": pedido.estado,
                "items": [
                    {
                        "productoId": str(i.producto_id),
                        "cantidad": i.cantidad,
                        "precioUnitario": float(i.precio_unitario),
                        "ivaUnitario": float(i.iva_unitario),
                        "subtotal": float(i.subtotal)
                    } for i in items
                ],
                "subtotalBase": float(pedido.subtotal_base),
                "totalIva": float(pedido.total_iva),
                "total": float(pedido.total),
                "fechaCreacion": pedido.fecha_creacion.isoformat()
            }
        }

    def actualizar_estado(self, pedido_id, nuevo_estado: str, rol: str) -> dict:
        ahora = datetime.now(timezone.utc)

        if rol != "administrador":
            raise HTTPException(status_code=403, detail={
                "success": False, "statusCode": 403,
                "message": "Acceso denegado",
                "error": {"error_code": "FORBIDDEN",
                          "details": "Solo un administrador puede actualizar el estado del pedido.",
                          "timestamp": ahora.isoformat()}
            })

        if nuevo_estado not in ESTADOS_VALIDOS and nuevo_estado != "cancelado":
            raise HTTPException(status_code=400, detail={
                "success": False, "statusCode": 400,
                "message": "El estado proporcionado no es válido",
                "error": {"error_code": "INVALID_ORDER_STATUS",
                          "details": "Los estados válidos son: pendiente, pagado, en_preparacion, enviado, entregado",
                          "timestamp": ahora.isoformat()}
            })

        pedido = self.pedido_repo.buscar_por_id(pedido_id)
        if not pedido:
            raise HTTPException(status_code=404, detail={
                "success": False, "statusCode": 404,
                "message": "Pedido no encontrado",
                "error": {"error_code": "ORDER_NOT_FOUND",
                          "details": "No existe un pedido con el ID proporcionado",
                          "timestamp": ahora.isoformat()}
            })

        if nuevo_estado == "cancelado":
            if pedido.estado in ESTADOS_NO_CANCELABLES:
                raise HTTPException(status_code=409, detail={
                    "success": False, "statusCode": 409,
                    "message": "El pedido no puede cancelarse en su estado actual",
                    "error": {"error_code": "ORDER_CANCELLATION_BLOCKED",
                              "details": "Una vez que el pedido está en preparación o en un estado posterior, no puede cancelarse.",
                              "timestamp": ahora.isoformat()}
                })
        else:
            siguiente_valido = FLUJO_ESTADOS.get(pedido.estado)
            if nuevo_estado != siguiente_valido:
                raise HTTPException(status_code=409, detail={
                    "success": False, "statusCode": 409,
                    "message": "Transición de estado no permitida",
                    "error": {"error_code": "INVALID_STATE_TRANSITION",
                              "details": f"El pedido está en estado '{pedido.estado}'. El único siguiente estado válido es '{siguiente_valido}'.",
                              "timestamp": ahora.isoformat()}
                })

        pedido_actualizado = self.pedido_repo.actualizar_estado(pedido, nuevo_estado)

        return {
            "success": True,
            "statusCode": 200,
            "message": "Estado del pedido actualizado correctamente",
            "data": {
                "pedidoId": str(pedido_actualizado.id),
                "estado": pedido_actualizado.estado,
                "fechaActualizacion": pedido_actualizado.fecha_actualizacion.isoformat()
            }
        }
