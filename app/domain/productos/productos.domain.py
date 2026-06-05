import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Numeric, ForeignKey, Date, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.base import Base


class Categoria(Base):
    __tablename__ = "categorias"
    __table_args__ = {'extend_existing': True}

    id     = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(100), nullable=False)
    codigo = Column(String(20),  nullable=False, unique=True)

    productos = relationship("Producto", back_populates="categoria")


class Laboratorio(Base):
    __tablename__ = "laboratorios"
    __table_args__ = {'extend_existing': True}

    id     = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(100), nullable=False, unique=True)
    pais   = Column(String(100), nullable=False)

    productos = relationship("Producto", back_populates="laboratorio")


class Producto(Base):
    __tablename__ = "productos"
    __table_args__ = {'extend_existing': True}

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre         = Column(String(200), nullable=False)
    descripcion    = Column(Text, nullable=True)
    precio         = Column(Numeric(10, 2), nullable=False)
    aplica_iva     = Column(Boolean, nullable=False, default=False)
    stock          = Column(Integer, nullable=False, default=0)
    activo         = Column(Boolean, nullable=False, default=False)
    categoria_id   = Column(UUID(as_uuid=True), ForeignKey("categorias.id"), nullable=False)
    laboratorio_id = Column(UUID(as_uuid=True), ForeignKey("laboratorios.id"), nullable=False)
    fecha_registro = Column(DateTime(timezone=True), nullable=False,
                            default=lambda: datetime.now(timezone.utc))

    categoria      = relationship("Categoria",   back_populates="productos")
    laboratorio    = relationship("Laboratorio", back_populates="productos")
    lotes          = relationship("Lote",         back_populates="producto")
    presentaciones = relationship("Presentacion", back_populates="producto")


class Lote(Base):
    __tablename__ = "lotes"
    __table_args__ = (
        CheckConstraint("cantidad >= 0", name="ck_lotes_cantidad"),
        {'extend_existing': True}
    )

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    producto_id       = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=False)
    codigo_lote       = Column(String(50), nullable=False, unique=True)
    cantidad          = Column(Integer, nullable=False, default=0)
    fecha_vencimiento = Column(Date, nullable=False)
    fecha_ingreso     = Column(DateTime(timezone=True), nullable=False,
                               default=lambda: datetime.now(timezone.utc))

    producto = relationship("Producto", back_populates="lotes")


class Presentacion(Base):
    __tablename__ = "presentaciones"
    __table_args__ = {'extend_existing': True}

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    producto_id = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=False)
    tipo        = Column(String(50), nullable=False)
    cantidad    = Column(Integer, nullable=False)
    unidad      = Column(String(20), nullable=False)

    producto = relationship("Producto", back_populates="presentaciones")