from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
import importlib.util, os

_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "domain", "carritos", "carritos.domain.py"))
_spec = importlib.util.spec_from_file_location("carritos_domain", _path)
_mod  = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
Carrito     = _mod.Carrito
ItemCarrito = _mod.ItemCarrito


class CarritoRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def buscar_activo_por_usuario_id(self, usuario_id):
        return (
            self.db.query(Carrito)
            .filter(Carrito.usuario_id == usuario_id, Carrito.activo == True)
            .first()
        )

    def guardar(self, carrito: Carrito) -> Carrito:
        self.db.add(carrito)
        self.db.commit()
        self.db.refresh(carrito)
        return carrito

    def actualizar_totales(self, carrito: Carrito, subtotal_base: Decimal, total_iva: Decimal, total: Decimal) -> Carrito:
        carrito.subtotal_base = subtotal_base
        carrito.total_iva     = total_iva
        carrito.total         = total
        self.db.commit()
        self.db.refresh(carrito)
        return carrito


class ItemCarritoRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def buscar_por_carrito_y_producto(self, carrito_id, producto_id):
        return (
            self.db.query(ItemCarrito)
            .filter(ItemCarrito.carrito_id == carrito_id, ItemCarrito.producto_id == producto_id)
            .first()
        )

    def guardar(self, item: ItemCarrito) -> ItemCarrito:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def buscar_por_id_y_usuario(self, item_id, usuario_id):
        return (
            self.db.query(ItemCarrito)
            .join(Carrito, ItemCarrito.carrito_id == Carrito.id)
            .filter(
                ItemCarrito.id == item_id,
                Carrito.usuario_id == usuario_id,
                Carrito.activo == True,
            )
            .first()
        )

    def actualizar_cantidad(self, item: ItemCarrito, cantidad: int, subtotal: Decimal) -> ItemCarrito:
        item.cantidad = cantidad
        item.subtotal = subtotal
        self.db.commit()
        self.db.refresh(item)
        return item

    def contar_productos_distintos(self, carrito_id) -> int:
        return (
            self.db.query(func.count(ItemCarrito.id))
            .filter(ItemCarrito.carrito_id == carrito_id)
            .scalar()
        )

    def eliminar(self, item: ItemCarrito) -> None:
        self.db.delete(item)
        self.db.commit()
