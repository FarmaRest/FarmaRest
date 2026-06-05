from sqlalchemy.orm import Session
from app.domain.carritos import Carrito, ItemCarrito


class CarritoRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def buscar_por_id(self, carrito_id) -> Carrito:
        return self.db.query(Carrito).filter(Carrito.id == carrito_id).first()

    def buscar_activo_por_usuario(self, usuario_id) -> Carrito:
        return self.db.query(Carrito).filter(
            Carrito.usuario_id == usuario_id,
            Carrito.activo == True
        ).first()

    def desactivar(self, carrito_id) -> None:
        carrito = self.db.query(Carrito).filter(Carrito.id == carrito_id).first()
        if carrito:
            carrito.activo = False
            self.db.flush()


class ItemCarritoRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def buscar_por_carrito_id(self, carrito_id) -> list:
        return self.db.query(ItemCarrito).filter(
            ItemCarrito.carrito_id == carrito_id
        ).all()