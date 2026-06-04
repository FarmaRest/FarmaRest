# ─────────────────────────────────────────────────────────────────────────────
# CAPA: DOMAIN — Módulo de Carritos
# Responsabilidad: Define los modelos ORM que SQLAlchemy mapea a tablas en la
# base de datos. Aquí viven las entidades del negocio y sus relaciones.
# Ninguna otra capa escribe SQL — solo define la estructura.
# ─────────────────────────────────────────────────────────────────────────────

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Boolean, DateTime, Integer, Numeric, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.base import Base


class Carrito(Base):
    """
    Tabla principal del módulo. Un usuario puede tener un carrito activo a la vez.
    subtotal_base, total_iva y total son calculados y actualizados por el servicio
    cada vez que se agrega, modifica o elimina un ítem.
    CASCADE: al eliminar el usuario se elimina su carrito automáticamente.
    """
    __tablename__ = "carritos"
    __table_args__ = (
        CheckConstraint("subtotal_base >= 0", name="ck_carritos_subtotal"),
        CheckConstraint("total_iva >= 0",     name="ck_carritos_iva"),
        CheckConstraint("total >= 0",         name="ck_carritos_total"),
    )

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # CASCADE: al eliminar el usuario se elimina su carrito automáticamente
    usuario_id    = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)

    # Totales calculados por el servicio al agregar/modificar ítems
    subtotal_base = Column(Numeric(10, 2), nullable=False, default=0)
    total_iva     = Column(Numeric(10, 2), nullable=False, default=0)
    total         = Column(Numeric(10, 2), nullable=False, default=0)

    # Un usuario solo puede tener un carrito activo a la vez — controlado por servicio
    activo        = Column(Boolean, nullable=False, default=True)

    fecha_creacion = Column(DateTime(timezone=True), nullable=False,
                            default=lambda: datetime.now(timezone.utc))

    # Relaciones
    usuario = relationship("Usuario", back_populates="carritos")

    # CASCADE: al eliminar el carrito se eliminan sus ítems automáticamente
    items   = relationship("ItemCarrito", back_populates="carrito", cascade="all, delete-orphan")


class ItemCarrito(Base):
    """
    Tabla de ítems dentro de un carrito. Cada fila es un producto agregado.
    precio_unitario e iva_unitario son snapshots del momento en que se agregó
    el producto — no cambian aunque el precio del producto cambie después.
    UNIQUE (carrito_id, producto_id): un producto no puede aparecer dos veces
    en el mismo carrito.
    """
    __tablename__ = "items_carrito"
    __table_args__ = (
        UniqueConstraint("carrito_id", "producto_id", name="uq_items_carrito_carrito_producto"),
        CheckConstraint("cantidad > 0",         name="ck_items_carrito_cantidad"),
        CheckConstraint("precio_unitario > 0",  name="ck_items_carrito_precio"),
        CheckConstraint("iva_unitario >= 0",    name="ck_items_carrito_iva"),
        CheckConstraint("subtotal > 0",         name="ck_items_carrito_subtotal"),
    )

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # CASCADE: al eliminar el carrito se eliminan sus ítems automáticamente
    carrito_id      = Column(UUID(as_uuid=True), ForeignKey("carritos.id", ondelete="CASCADE"), nullable=False)

    # Sin CASCADE: no se puede eliminar un producto que esté en un carrito activo
    producto_id     = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=False)

    cantidad        = Column(Integer,       nullable=False)

    # Snapshot del precio base sin IVA al momento de agregar al carrito
    precio_unitario = Column(Numeric(10, 2), nullable=False)

    # IVA por unidad: precio_unitario × 0.19 si aplica_iva = true, sino 0
    iva_unitario    = Column(Numeric(10, 2), nullable=False, default=0)

    # subtotal = cantidad × (precio_unitario + iva_unitario)
    subtotal        = Column(Numeric(10, 2), nullable=False)

    # Relaciones
    carrito  = relationship("Carrito",  back_populates="items")
    producto = relationship("Producto")
