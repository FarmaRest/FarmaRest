from sqlalchemy.orm import Session
from app.domain.pedidos import Pedido, ItemPedido


class PedidoRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def guardar(self, pedido: Pedido) -> Pedido:
        self.db.add(pedido)
        self.db.flush()
        return pedido

    def buscar_por_id(self, pedido_id) -> Pedido:
        return self.db.query(Pedido).filter(Pedido.id == pedido_id).first()

    def buscar_por_usuario_id(self, usuario_id) -> list:
        return self.db.query(Pedido).filter(
            Pedido.usuario_id == usuario_id
        ).order_by(Pedido.fecha_creacion.desc()).all()

    def listar_todos(self) -> list:
        return self.db.query(Pedido).order_by(Pedido.fecha_creacion.desc()).all()


class ItemPedidoRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def guardar_todos(self, items: list) -> list:
        for item in items:
            self.db.add(item)
        self.db.flush()
        return items

    def buscar_por_pedido_id(self, pedido_id) -> list:
        return self.db.query(ItemPedido).filter(
            ItemPedido.pedido_id == pedido_id
        ).all()