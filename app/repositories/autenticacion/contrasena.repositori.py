from sqlalchemy.orm import Session
from datetime import datetime, timezone
import importlib.util, os, uuid

_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "domain", "usuarios", "usuarios.domain.py"))
_spec = importlib.util.spec_from_file_location("usuarios_domain", _path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
HistorialContrasena = _mod.HistorialContrasena


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