from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
import importlib.util, os

_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "app", "services", "autenticacion", "autenticacion.services.py"))
_spec = importlib.util.spec_from_file_location("autenticacion_services", _path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
AutenticacionService = _mod.AutenticacionService

router = APIRouter(prefix="/auth", tags=["Autenticacion"])


class LoginRequest(BaseModel):
    correo: str
    contrasena: str


class LogoutRequest(BaseModel):
    refreshToken: str


class RefreshTokenRequest(BaseModel):
    refreshToken: str


class CambiarContrasenaRequest(BaseModel):
    correo: str
    contrasenaActual: str
    contrasenaNueva: str


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
    return service.cambiar_contrasena(request.correo, request.contrasenaActual, request.contrasenaNueva)