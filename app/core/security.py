import os
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.domain.usuarios import Usuario

SECRET_KEY = os.getenv("SECRET_KEY", "cambia-este-valor-en-produccion")
ALGORITHM = "HS256"

_bearer = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        usuario_id: str = payload.get("sub")
        if not usuario_id:
            raise ValueError("sin sub")
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "statusCode": 401,
                "message": "Token inválido o expirado",
                "error": {
                    "error_code": "INVALID_TOKEN",
                    "details": "El token de acceso no es válido o ha expirado.",
                },
            },
        )

    usuario = db.query(Usuario).filter(Usuario.id == uuid.UUID(usuario_id)).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "statusCode": 401,
                "message": "Usuario no encontrado",
                "error": {
                    "error_code": "USER_NOT_FOUND",
                    "details": "El usuario asociado al token no existe.",
                },
            },
        )
    if usuario.estado != "activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "statusCode": 403,
                "message": "Tu cuenta se encuentra inactiva",
                "error": {
                    "error_code": "ACCOUNT_INACTIVE",
                    "details": "Tu cuenta fue marcada como inactiva. Contacta al administrador.",
                },
            },
        )
    return usuario
