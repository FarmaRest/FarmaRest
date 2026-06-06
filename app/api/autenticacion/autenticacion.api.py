from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from jose import jwt, JWTError
import os
import importlib.util

from app.core.database import get_db

# Cargar servicio
_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "services", "autenticacion", "autenticacion.services.py"))
_spec = importlib.util.spec_from_file_location("autenticacion_services", _path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
AutenticacionService = _mod.AutenticacionService

# Cargar repositorio de usuarios
_path_usr = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "repositories", "usuarios", "usuarios.repositori.py"))
_spec_usr = importlib.util.spec_from_file_location("usuarios_repositori", _path_usr)
_mod_usr = importlib.util.module_from_spec(_spec_usr)
_spec_usr.loader.exec_module(_mod_usr)
UsuarioRepositorio = _mod_usr.UsuarioRepositorio

SECRET_KEY = os.getenv("SECRET_KEY", "cambia-este-valor-en-produccion")
ALGORITHM = "HS256"
security = HTTPBearer()

router = APIRouter(prefix="/autenticacion", tags=["Autenticacion"])


def get_usuario_actual(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        usuario_id = payload.get("sub")
        if not usuario_id:
            raise HTTPException(status_code=401, detail={"success": False, "statusCode": 401, "message": "Token inválido", "error": {"error_code": "INVALID_TOKEN"}})
    except JWTError:
        raise HTTPException(status_code=401, detail={"success": False, "statusCode": 401, "message": "Token inválido o expirado", "error": {"error_code": "INVALID_TOKEN"}})
    repo = UsuarioRepositorio(db)
    usuario = repo.buscar_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=401, detail={"success": False, "statusCode": 401, "message": "Usuario no encontrado", "error": {"error_code": "USER_NOT_FOUND"}})
    return usuario


class LoginRequest(BaseModel):
    correo: str
    contrasena: str


class LogoutRequest(BaseModel):
    refreshToken: str


class RefreshTokenRequest(BaseModel):
    refreshToken: str


class CambiarContrasenaRequest(BaseModel):
    correo: str
    contrasena_actual: str
    contrasena_nueva: str


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    service = AutenticacionService(db)
    return service.login(request.correo, request.contrasena)


@router.post("/logout")
def logout(request: LogoutRequest, db: Session = Depends(get_db)):
    service = AutenticacionService(db)
    return service.logout(request.refreshToken)


@router.post("/refresh-token")
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    service = AutenticacionService(db)
    return service.refresh_token(request.refreshToken)


@router.patch("/cambiar-contrasena")
def cambiar_contrasena(request: CambiarContrasenaRequest, db: Session = Depends(get_db)):
    service = AutenticacionService(db)
    return service.cambiar_contrasena(request.correo, request.contrasena_actual, request.contrasena_nueva)
