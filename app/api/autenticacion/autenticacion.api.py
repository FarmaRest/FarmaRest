from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
import importlib.util, os

_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "app", "services", "autenticacion", "autenticacion.services.py"))
_spec = importlib.util.spec_from_file_location("autenticacion_services", _path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
AutenticacionService = _mod.AutenticacionService

router = APIRouter(prefix="/autenticacion", tags=["Autenticacion"])

class LoginRequest(BaseModel):
    usuario_id: int

class TokenResponse(BaseModel):
    token: str

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    service = AutenticacionService(db)
    token = service.crear_token_acceso(request.usuario_id)
    return {"token": token}

@router.post("/logout")
def logout(token: str, db: Session = Depends(get_db)):
    service = AutenticacionService(db)
    resultado = service.cerrar_sesion(token)
    if not resultado:
        raise HTTPException(status_code=404, detail="Token no encontrado")
    return {"mensaje": "Sesión cerrada correctamente"}

@router.get("/verificar")
def verificar(token: str, db: Session = Depends(get_db)):
    service = AutenticacionService(db)
    payload = service.verificar_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return {"valido": True, "datos": payload}