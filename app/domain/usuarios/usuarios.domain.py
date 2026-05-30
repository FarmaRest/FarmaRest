# ─────────────────────────────────────────────────────────────────────────────
# CAPA: DOMAIN — Módulo de Usuarios
# Responsabilidad: Define los modelos ORM que SQLAlchemy mapea a tablas en la
# base de datos. Aquí viven las entidades del negocio y sus relaciones.
# Ninguna otra capa escribe SQL — solo define la estructura.
# ─────────────────────────────────────────────────────────────────────────────

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.base import Base


class Usuario(Base):
    """
    Tabla principal del módulo. Almacena todos los datos personales del usuario.
    La contraseña NUNCA se guarda en texto plano, solo el hash bcrypt.
    El correo y la cédula son únicos en todo el sistema.
    """
    __tablename__ = "usuarios"

    # Identificador único universal, se genera automáticamente al crear el registro
    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Nombres y apellidos separados para facilitar búsquedas y reportes
    primer_nombre    = Column(String(50),  nullable=False)
    segundo_nombre   = Column(String(50),  nullable=True)
    primer_apellido  = Column(String(50),  nullable=False)
    segundo_apellido = Column(String(50),  nullable=True)

    # Datos de identificación — ambos únicos en el sistema
    cedula           = Column(String(20),  nullable=False, unique=True)
    correo           = Column(String(150), nullable=False, unique=True)

    # Nunca se almacena la contraseña real, solo el hash generado con bcrypt
    hash_contrasena  = Column(String,      nullable=False)
    telefono         = Column(String(20),  nullable=True)

    # Rol por defecto: cliente. También puede ser admin
    rol              = Column(String(20),  nullable=False, default="cliente")

    # Estado por defecto: activo. Puede pasar a inactivo por el cron de HU-USR-04
    estado           = Column(String(20),  nullable=False, default="activo")

    # Se establece automáticamente al momento de crear el registro
    fecha_registro   = Column(DateTime(timezone=True), nullable=False,
                              default=lambda: datetime.now(timezone.utc))

    # Relaciones
    direcciones       = relationship("Direccion",       back_populates="usuario", cascade="all, delete-orphan")
    historial_correos = relationship("HistorialCorreo", back_populates="usuario", cascade="all, delete-orphan")
    sesiones          = relationship("Sesion",          back_populates="usuario", cascade="all, delete-orphan")


class Direccion(Base):
    """
    Tabla de direcciones de entrega del usuario.
    Un usuario puede tener múltiples direcciones pero solo una marcada como principal.
    """
    __tablename__ = "direcciones"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id   = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    direccion    = Column(String(200), nullable=False)
    departamento = Column(String(100), nullable=False)
    ciudad       = Column(String(100), nullable=False)
    principal    = Column(Boolean, nullable=False, default=False)

    usuario = relationship("Usuario", back_populates="direcciones")


class HistorialCorreo(Base):
    """
    Tabla de auditoría de cambios de correo.
    """
    __tablename__ = "historial_correos"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id      = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    correo_anterior = Column(String(150), nullable=False)
    fecha_cambio    = Column(DateTime(timezone=True), nullable=False,
                             default=lambda: datetime.now(timezone.utc))

    usuario = relationship("Usuario", back_populates="historial_correos")