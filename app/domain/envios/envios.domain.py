# ─────────────────────────────────────────────────────────────────────────────
# CAPA: DOMAIN — Módulo de Envíos
# Responsabilidad: Define los modelos ORM que SQLAlchemy mapea a tablas en la
# base de datos. Aquí viven las entidades del negocio y sus relaciones.
# Ninguna otra capa escribe SQL — solo define la estructura.
# ─────────────────────────────────────────────────────────────────────────────

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Date, Numeric, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.base import Base


class Envio(Base):
    """
    Tabla del módulo de envíos. Registra cada despacho generado tras un pago aprobado.
    La restricción UNIQUE en pedido_id garantiza que un pedido tenga exactamente un envío.
    Las FK sin CASCADE protegen la integridad: no se pueden eliminar pedidos o usuarios
    que tengan envíos activos.
    """
    __tablename__ = "envios"
    __table_args__ = (
        CheckConstraint("costo_envio >= 0", name="ck_envios_costo"),
    )

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # UNIQUE: un pedido genera exactamente un envío — segunda capa de validación además del servicio
    pedido_id           = Column(UUID(as_uuid=True), ForeignKey("pedidos.id"), nullable=False, unique=True)
    usuario_id          = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Estado logístico del envío
    estado              = Column(String(20),    nullable=False, default="en_preparacion")

    direccion_entrega   = Column(String(200),   nullable=False)
    ciudad_entrega      = Column(String(100),   nullable=False)
    empresa_transporte  = Column(String(100),   nullable=False)

    # Fecha programada de despacho — tipo Date (solo fecha, sin hora)
    fecha_despacho      = Column(Date,          nullable=False)

    # Costo en pesos COP con dos decimales. CHECK >= 0 evita valores negativos en BD
    costo_envio         = Column(Numeric(10, 2), nullable=False, default=0)

    fecha_creacion      = Column(DateTime(timezone=True), nullable=False,
                                 default=lambda: datetime.now(timezone.utc))
    fecha_actualizacion = Column(DateTime(timezone=True), nullable=False,
                                 default=lambda: datetime.now(timezone.utc),
                                 onupdate=lambda: datetime.now(timezone.utc))

    # Relaciones
    pedido  = relationship("Pedido")
    usuario = relationship("Usuario")
