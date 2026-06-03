from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt
import os
import importlib.util

_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "repositories", "autenticacion", "autenticacion.repositori.py"))
_spec = importlib.util.spec_from_file_location("autenticacion_repositori", _path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
TokenRepositorio = _mod.TokenRepositorio

SECRET_KEY = os.getenv("SECRET_KEY", "cambia-este-valor-en-produccion")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

class AutenticacionService:
    def __init__(self, db: Session):
        self.repositorio = TokenRepositorio(db)

    def crear_token_acceso(self, usuario_id: int) -> str:
        expiracion = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        datos = {"sub": str(usuario_id), "exp": expiracion}
        token = jwt.encode(datos, SECRET_KEY, algorithm=ALGORITHM)
        self.repositorio.crear_token(usuario_id, token, expiracion)
        return token

    def verificar_token(self, token: str) -> dict:
        registro = self.repositorio.obtener_token(token)
        if not registro:
            return None
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except Exception:
            return None

    def cerrar_sesion(self, token: str) -> bool:
        resultado = self.repositorio.desactivar_token(token)
        return resultado is not None