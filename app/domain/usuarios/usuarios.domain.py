import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.base import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = {'extend_existing': True}

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    primer_nombre    = Column(String(50),  nullable=False)
    segundo_nombre   = Column(String(50),  nullable=True)
    primer_apellido  = Column(String(50),  nullable=False)
    segundo_apellido = Column(String(50),  nullable=True)
    cedula           = Column(String(20),  nullable=False, unique=True)
    correo           = Column(String(150), nullable=False, unique=True)
    hash_contrasena  = Column(String,      nullable=False)
    telefono         = Column(String(20),  nullable=True)
    rol              = Column(String(20),  nullable=False, default="cliente")
    estado           = Column(String(20),  nullable=False, default="activo")
    fecha_registro   = Column(DateTime(timezone=True), nullable=False,
                              default=lambda: datetime.now(timezone.utc))
    fecha_cambio_contrasena = Column(DateTime(timezone=True), nullable=True)

    direcciones           = relationship("Direccion",           back_populates="usuario", cascade="all, delete-orphan")
    historial_correos     = relationship("HistorialCorreo",     back_populates="usuario", cascade="all, delete-orphan")
    sesiones              = relationship("Sesion",              back_populates="usuario", cascade="all, delete-orphan")
    carritos              = relationship("Carrito",             back_populates="usuario", cascade="all, delete-orphan")
    pedidos               = relationship("Pedido",              back_populates="usuario")
    historial_contrasenas = relationship("HistorialContrasena", back_populates="usuario", cascade="all, delete-orphan")


class Direccion(Base):
    __tablename__ = "direcciones"
    __table_args__ = {'extend_existing': True}

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id   = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    direccion    = Column(String(200), nullable=False)
    departamento = Column(String(100), nullable=False)
    ciudad       = Column(String(100), nullable=False)
    principal    = Column(Boolean, nullable=False, default=False)

    usuario = relationship("Usuario", back_populates="direcciones")


class HistorialCorreo(Base):
    __tablename__ = "historial_correos"
    __table_args__ = {'extend_existing': True}

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id      = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    correo_anterior = Column(String(150), nullable=False)
    fecha_cambio    = Column(DateTime(timezone=True), nullable=False,
                             default=lambda: datetime.now(timezone.utc))

    usuario = relationship("Usuario", back_populates="historial_correos")


class HistorialContrasena(Base):
    __tablename__ = "historial_contrasenas"
    __table_args__ = {'extend_existing': True}

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id      = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    hash_contrasena = Column(String, nullable=False)
    fecha_cambio    = Column(DateTime(timezone=True), nullable=False,
                             default=lambda: datetime.now(timezone.utc))

    usuario = relationship("Usuario", back_populates="historial_contrasenas")
