# ─────────────────────────────────────────────────────────────────────────────
# CAPA: DOMAIN — Módulo de Pedidos
# ─────────────────────────────────────────────────────────────────────────────

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Numeric, Integer, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.base import Base


class Pedido(Base):
    __tablename__ = "pedidos"
    __table_args__ = (
        CheckConstraint("subtotal_base > 0", name="ck_pedidos_subtotal"),
        CheckConstraint("total_iva >= 0",    name="ck_pedidos_iva"),
        CheckConstraint("total > 0",         name="ck_pedidos_total"),
        {'extend_existing': True}
    )

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id          = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    carrito_id          = Column(UUID(as_uuid=True), ForeignKey("carritos.id"), nullable=False)
    estado              = Column(String(20),    nullable=False, default="pendiente")
    subtotal_base       = Column(Numeric(10, 2), nullable=False)
    total_iva           = Column(Numeric(10, 2), nullable=False, default=0)
    total               = Column(Numeric(10, 2), nullable=False)
    direccion_entrega   = Column(String(200),   nullable=False)
    ciudad_entrega      = Column(String(100),   nullable=False)
    metodo_pago         = Column(String(50),    nullable=False)
    fecha_creacion      = Column(DateTime(timezone=True), nullable=False,
                                 default=lambda: datetime.now(timezone.utc))
    fecha_actualizacion = Column(DateTime(timezone=True), nullable=False,
                                 default=lambda: datetime.now(timezone.utc),
                                 onupdate=lambda: datetime.now(timezone.utc))

    usuario = relationship("Usuario", back_populates="pedidos")
    carrito = relationship("Carrito")
    items   = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")


class ItemPedido(Base):
    __tablename__ = "items_pedido"
    __table_args__ = (
        CheckConstraint("cantidad > 0",         name="ck_items_pedido_cantidad"),
        CheckConstraint("precio_unitario > 0",  name="ck_items_pedido_precio"),
        CheckConstraint("iva_unitario >= 0",    name="ck_items_pedido_iva"),
        CheckConstraint("subtotal > 0",         name="ck_items_pedido_subtotal"),
        {'extend_existing': True}
    )

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id       = Column(UUID(as_uuid=True), ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False)
    producto_id     = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=False)
    cantidad        = Column(Integer,        nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    iva_unitario    = Column(Numeric(10, 2), nullable=False, default=0)
    subtotal        = Column(Numeric(10, 2), nullable=False)

    pedido   = relationship("Pedido",   back_populates="items")
    producto = relationship("Producto")