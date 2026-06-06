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