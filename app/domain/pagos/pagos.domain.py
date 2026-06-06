# ─────────────────────────────────────────────────────────────────────────────
# CAPA: DOMAIN — Módulo de Pagos
# Responsabilidad: Define los modelos ORM que SQLAlchemy mapea a tablas en la
# base de datos. Aquí viven las entidades del negocio y sus relaciones.
# Ninguna otra capa escribe SQL — solo define la estructura.
# ─────────────────────────────────────────────────────────────────────────────

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, BigInteger, Numeric, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.base import Base


class Pago(Base):
    """
    Tabla principal del módulo. Registra cada transacción iniciada con Wompi.
    El pago nace en estado PENDING y Wompi lo actualiza via webhook.
    La referencia_interna es el campo que se cruza con el webhook para identificar
    a qué pedido pertenece la respuesta de Wompi.
    """
    __tablename__ = "pagos"
    __table_args__ = (
        CheckConstraint("monto_en_centavos > 0", name="ck_pagos_monto"),
    )

    id                   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Claves foráneas hacia pedidos y usuarios
    pedido_id            = Column(UUID(as_uuid=True), ForeignKey("pedidos.id"), nullable=False)
    usuario_id           = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Identificador interno del pago — formato FARMA-PED-XXX-XXX, único por pago
    referencia_interna   = Column(String(100), nullable=False, unique=True)

    # ID retornado por Wompi al confirmar. Llega NULL hasta que Wompi responde via webhook
    id_transaccion_wompi = Column(String(100), nullable=True, unique=True)

    # Wompi trabaja en centavos: $9.000 COP = 900000 centavos. BigInt para evitar overflow
    monto_en_centavos    = Column(BigInteger, nullable=False)

    moneda               = Column(String(10),  nullable=False, default="COP")

    # Método confirmado por Wompi (ej. CARD). NULL hasta que Wompi responde
    metodo_pago          = Column(String(50),  nullable=True)

    # Estado de la transacción según Wompi
    estado_transaccion   = Column(String(20),  nullable=False, default="PENDING")

    # URL de pago generada por Wompi para redirigir al usuario al checkout
    url_checkout         = Column(Text, nullable=True)

    fecha_creacion       = Column(DateTime(timezone=True), nullable=False,
                                  default=lambda: datetime.now(timezone.utc))
    fecha_actualizacion  = Column(DateTime(timezone=True), nullable=False,
                                  default=lambda: datetime.now(timezone.utc),
                                  onupdate=lambda: datetime.now(timezone.utc))

    # Relaciones
    pedido  = relationship("Pedido")
    usuario = relationship("Usuario")

    # Relación 1 a 1 con Factura: un pago aprobado genera exactamente una factura
    factura = relationship("Factura", back_populates="pago", uselist=False)


class Factura(Base):
    """
    Tabla de facturas electrónicas generadas tras un pago aprobado.
    Se integra con Factus para emitir la factura ante la DIAN.
    El cufe es el Código Único de Factura Electrónica que retorna la DIAN.
    """
    __tablename__ = "facturas"
    __table_args__ = (
        CheckConstraint("subtotal_base > 0", name="ck_facturas_subtotal"),
        CheckConstraint("total_iva >= 0",    name="ck_facturas_iva"),
        CheckConstraint("total > 0",         name="ck_facturas_total"),
    )

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # CASCADE: si se elimina el pago, la factura se elimina automáticamente
    pago_id        = Column(UUID(as_uuid=True), ForeignKey("pagos.id", ondelete="CASCADE"),
                            nullable=False, unique=True)
    pedido_id      = Column(UUID(as_uuid=True), ForeignKey("pedidos.id"), nullable=False)
    usuario_id     = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Número secuencial único generado por el sistema
    numero_factura = Column(String(50),    nullable=False, unique=True)

    # Valores monetarios en pesos colombianos con dos decimales
    subtotal_base  = Column(Numeric(10, 2), nullable=False)
    total_iva      = Column(Numeric(10, 2), nullable=False, default=0)
    total          = Column(Numeric(10, 2), nullable=False)

    # Campos de integración con Factus/DIAN — llegan NULL hasta que Factus confirma
    cufe           = Column(String(200), nullable=True)
    factus_id      = Column(String(100), nullable=True)
    url_pdf        = Column(Text, nullable=True)
    url_xml        = Column(Text, nullable=True)

    # Estado de la emisión ante la DIAN
    estado_dian    = Column(String(20),  nullable=False, default="pendiente")

    fecha_emision  = Column(DateTime(timezone=True), nullable=False,
                            default=lambda: datetime.now(timezone.utc))

    # Relaciones
    pago    = relationship("Pago", back_populates="factura")
    pedido  = relationship("Pedido")
    usuario = relationship("Usuario")
