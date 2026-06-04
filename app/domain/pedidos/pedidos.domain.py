# ─────────────────────────────────────────────────────────────────────────────
# CAPA: DOMAIN — Módulo de Pedidos
# Responsabilidad: Define los modelos ORM que SQLAlchemy mapea a tablas en la
# base de datos. Aquí viven las entidades del negocio y sus relaciones.
# Ninguna otra capa escribe SQL — solo define la estructura.
# ─────────────────────────────────────────────────────────────────────────────

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Numeric, Integer, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.base import Base


class Pedido(Base):
    """
    Tabla principal del módulo. Registra cada orden de compra generada desde un carrito.
    FK hacia usuarios SIN CASCADE: un usuario con pedidos no puede eliminarse —
    esto protege el historial financiero del negocio.
    FK hacia carritos SIN CASCADE: el carrito queda referenciado por el pedido
    para trazabilidad.
    """
    __tablename__ = "pedidos"
    __table_args__ = (
        CheckConstraint("subtotal_base > 0", name="ck_pedidos_subtotal"),
        CheckConstraint("total_iva >= 0",    name="ck_pedidos_iva"),
        CheckConstraint("total > 0",         name="ck_pedidos_total"),
    )

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Sin CASCADE: no se puede eliminar un usuario que tenga pedidos
    usuario_id          = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Sin CASCADE: el carrito queda referenciado para trazabilidad
    carrito_id          = Column(UUID(as_uuid=True), ForeignKey("carritos.id"), nullable=False)

    # Ciclo de vida del pedido
    estado              = Column(String(20),    nullable=False, default="pendiente")

    # Totales calculados al crear el pedido desde el carrito
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

    # Relaciones
    usuario = relationship("Usuario", back_populates="pedidos")
    carrito = relationship("Carrito")

    # CASCADE: al eliminar el pedido se eliminan sus ítems automáticamente
    items   = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")


class ItemPedido(Base):
    """
    Tabla de ítems de un pedido. Snapshot definitivo del precio e IVA al momento
    de crear el pedido — inmutable ante cualquier cambio posterior en el producto.
    CASCADE: al eliminar el pedido se eliminan sus ítems automáticamente.
    """
    __tablename__ = "items_pedido"
    __table_args__ = (
        CheckConstraint("cantidad > 0",         name="ck_items_pedido_cantidad"),
        CheckConstraint("precio_unitario > 0",  name="ck_items_pedido_precio"),
        CheckConstraint("iva_unitario >= 0",    name="ck_items_pedido_iva"),
        CheckConstraint("subtotal > 0",         name="ck_items_pedido_subtotal"),
    )

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # CASCADE: al eliminar el pedido se eliminan sus ítems automáticamente
    pedido_id       = Column(UUID(as_uuid=True), ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False)

    # Sin CASCADE: no se puede eliminar un producto que tenga ítems en pedidos
    producto_id     = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=False)

    cantidad        = Column(Integer,        nullable=False)

    # Snapshot del precio base sin IVA al momento exacto de crear el pedido
    precio_unitario = Column(Numeric(10, 2), nullable=False)

    # IVA por unidad: precio_unitario × 0.19 si aplica_iva = true, sino 0
    iva_unitario    = Column(Numeric(10, 2), nullable=False, default=0)

    # subtotal = cantidad × (precio_unitario + iva_unitario)
    subtotal        = Column(Numeric(10, 2), nullable=False)

    # Relaciones
    pedido   = relationship("Pedido",   back_populates="items")
    producto = relationship("Producto")
