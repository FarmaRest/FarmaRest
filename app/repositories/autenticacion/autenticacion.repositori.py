from sqlalchemy.orm import Session
from datetime import datetime
import importlib.util, os

_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "domain", "autenticacion", "autenticacion.domain.py"))
_spec = importlib.util.spec_from_file_location("autenticacion_domain", _path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
Token = _mod.Token

class TokenRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def crear_token(self, usuario_id: int, token: str, fecha_expiracion: datetime):
        nuevo_token = Token(
            usuario_id=usuario_id,
            token=token,
            fecha_expiracion=fecha_expiracion
        )
        self.db.add(nuevo_token)
        self.db.commit()
        self.db.refresh(nuevo_token)
        return nuevo_token

    def obtener_token(self, token: str):
        return self.db.query(Token).filter(Token.token == token, Token.activo == True).first()

    def desactivar_token(self, token: str):
        registro = self.obtener_token(token)
        if registro:
            registro.activo = False
            self.db.commit()
        return registro