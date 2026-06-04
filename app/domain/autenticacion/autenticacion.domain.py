import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.base import Base

class Sesion(Base):
    __tablename__ = "sesiones"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    access_token = Column(String, nullable=False, unique=True)
    refresh_token = Column(String, nullable=False, unique=True)
    fecha_expiracion_access = Column(DateTime(timezone=True), nullable=False)
    fecha_expiracion_refresh = Column(DateTime(timezone=True), nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    activa = Column(Boolean, nullable=False, default=True)

    usuario = relationship("Usuario", back_populates="sesiones")