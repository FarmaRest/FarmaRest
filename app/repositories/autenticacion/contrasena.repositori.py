# ─────────────────────────────────────────────────────────────────────────────
# CAPA: REPOSITORY – Historial de Contraseñas
# ─────────────────────────────────────────────────────────────────────────────

from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid
from app.domain.usuarios import HistorialContrasena


class HistorialContrasenaRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def guardar(self, usuario_id, hash_contrasena: str) -> HistorialContrasena:
        registro = HistorialContrasena(
            id=uuid.uuid4(),
            usuario_id=usuario_id,
            hash_contrasena=hash_contrasena,
            fecha_cambio=datetime.now(timezone.utc)
        )
        self.db.add(registro)
        self.db.commit()
        self.db.refresh(registro)
        return registro

    def buscar_por_usuario_id(self, usuario_id) -> list:
        return self.db.query(HistorialContrasena).filter(
            HistorialContrasena.usuario_id == usuario_id
        ).order_by(HistorialContrasena.fecha_cambio.desc()).all()
