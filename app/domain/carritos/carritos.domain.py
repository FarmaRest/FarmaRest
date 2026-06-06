import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Boolean, DateTime, Integer, Numeric, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.base import Base


class Carrito(Base):
    __tablename__ = "carritos"
    __table_args__ = (
        CheckConstraint("subtotal_base >= 0", name="ck_carritos_subtotal"),
        CheckConstraint("total_iva >= 0",     name="ck_carritos_iva"),
        CheckConstraint("total >= 0",         name="ck_carritos_total"),
        {'extend_existing': True}
    )

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id    = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    subtotal_base = Column(Numeric(10, 2), nullable=False, default=0)
    total_iva     = Column(Numeric(10, 2), nullable=False, default=0)
    total         = Column(Numeric(10, 2), nullable=False, default=0)
    activo        = Column(Boolean, nullable=False, default=True)
    fecha_creacion = Column(DateTime(timezone=True), nullable=False,
                            default=lambda: datetime.now(timezone.utc))

    usuario = relationship("Usuario", back_populates="carritos")
    items   = relationship("ItemCarrito", back_populates="carrito", cascade="all, delete-orphan")


class ItemCarrito(Base):
    __tablename__ = "items_carrito"
    __table_args__ = (
        UniqueConstraint("carrito_id", "producto_id", name="uq_items_carrito_carrito_producto"),
        CheckConstraint("cantidad > 0",         name="ck_items_carrito_cantidad"),
        CheckConstraint("precio_unitario > 0",  name="ck_items_carrito_precio"),
        CheckConstraint("iva_unitario >= 0",    name="ck_items_carrito_iva"),
        CheckConstraint("subtotal > 0",         name="ck_items_carrito_subtotal"),
        {'extend_existing': True}
    )

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    carrito_id      = Column(UUID(as_uuid=True), ForeignKey("carritos.id", ondelete="CASCADE"), nullable=False)
    producto_id     = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=False)
    cantidad        = Column(Integer,       nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    iva_unitario    = Column(Numeric(10, 2), nullable=False, default=0)
    subtotal        = Column(Numeric(10, 2), nullable=False)

    carrito  = relationship("Carrito",  back_populates="items")
    producto = relationship("Producto")