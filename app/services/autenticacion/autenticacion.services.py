from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from jose import jwt
from fastapi import HTTPException
import bcrypt
import os
import importlib.util
import uuid

# Cargar repositorio de autenticacion
_path_repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "repositories", "autenticacion", "autenticacion.repositori.py"))
_spec_repo = importlib.util.spec_from_file_location("autenticacion_repositori", _path_repo)
_mod_repo = importlib.util.module_from_spec(_spec_repo)
_spec_repo.loader.exec_module(_mod_repo)
AutenticacionRepositorio = _mod_repo.AutenticacionRepositorio

# Cargar repositorio de usuarios
_path_usr = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "repositories", "usuarios", "usuarios.repositori.py"))
_spec_usr = importlib.util.spec_from_file_location("usuarios_repositori", _path_usr)
_mod_usr = importlib.util.module_from_spec(_spec_usr)
_spec_usr.loader.exec_module(_mod_usr)
UsuarioRepositorio = _mod_usr.UsuarioRepositorio

# Cargar modelo Sesion
_path_dom = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "domain", "autenticacion", "autenticacion.domain.py"))
_spec_dom = importlib.util.spec_from_file_location("autenticacion_domain", _path_dom)
_mod_dom = importlib.util.module_from_spec(_spec_dom)
_spec_dom.loader.exec_module(_mod_dom)
Sesion = _mod_dom.Sesion

SECRET_KEY = os.getenv("SECRET_KEY", "cambia-este-valor-en-produccion")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7


class AutenticacionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AutenticacionRepositorio(db)
        self.usuario_repo = UsuarioRepositorio(db)

    def login(self, correo: str, contrasena: str) -> dict:
        usuario = self.usuario_repo.buscar_por_correo(correo)
        if not usuario:
            raise HTTPException(status_code=404, detail={
                "success": False,
                "statusCode": 404,
                "message": "Usuario no encontrado",
                "error": {
                    "error_code": "USER_NOT_FOUND",
                    "details": "No existe una cuenta registrada con ese correo electrónico"
                }
            })
        if usuario.estado == "inactivo":
            raise HTTPException(status_code=403, detail={
                "success": False,
                "statusCode": 403,
                "message": "Tu cuenta se encuentra inactiva",
                "error": {
                    "error_code": "ACCOUNT_INACTIVE",
                    "details": "Tu cuenta fue marcada como inactiva. Contacta al administrador para reactivarla."
                }
            })
        if not bcrypt.checkpw(contrasena.encode("utf-8"), usuario.hash_contrasena.encode("utf-8")):
            raise HTTPException(status_code=401, detail={
                "success": False,
                "statusCode": 401,
                "message": "Credenciales inválidas",
                "error": {
                    "error_code": "INVALID_CREDENTIALS",
                    "message": "El correo o la contraseña ingresados son incorrectos"
                }
            })
        ahora = datetime.now(timezone.utc)
        fecha_exp_access = ahora + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        fecha_exp_refresh = ahora + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        access_token = jwt.encode({"sub": str(usuario.id), "exp": fecha_exp_access}, SECRET_KEY, algorithm=ALGORITHM)
        refresh_token = jwt.encode({"sub": str(usuario.id), "exp": fecha_exp_refresh, "type": "refresh"}, SECRET_KEY, algorithm=ALGORITHM)

        sesion = Sesion(
            id=uuid.uuid4(),
            usuario_id=usuario.id,
            access_token=access_token,
            refresh_token=refresh_token,
            fecha_expiracion_access=fecha_exp_access,
            fecha_expiracion_refresh=fecha_exp_refresh,
            activa=True
        )
        self.repo.guardar(sesion)

        return {
            "success": True,
            "statusCode": 200,
            "message": "Inicio de sesión exitoso",
            "data": {
                "usuarioId": str(usuario.id),
                "nombre": f"{usuario.primer_nombre} {usuario.primer_apellido}",
                "correo": usuario.correo,
                "rol": usuario.rol,
                "accessToken": access_token,
                "refreshToken": refresh_token,
                "expiresIn": 3600
            }
        }

    def logout(self, refresh_token: str) -> dict:
        sesion = self.repo.buscar_por_refresh_token(refresh_token)
        if not sesion:
            raise HTTPException(status_code=401, detail={
                "success": False,
                "statusCode": 401,
                "message": "Token inválido o expirado",
                "error": {
                    "error_code": "INVALID_TOKEN",
                    "details": "El token proporcionado no es válido o ya expiró"
                }
            })
        self.repo.desactivar_sesion(sesion.id)
        return {
            "success": True,
            "statusCode": 200,
            "message": "Sesión cerrada correctamente",
            "data": None
        }

    def refresh_token(self, refresh_token: str) -> dict:
        sesion = self.repo.buscar_por_refresh_token(refresh_token)
        if not sesion:
            raise HTTPException(status_code=401, detail={
                "success": False,
                "statusCode": 401,
                "message": "El refresh token ha expirado. Debe iniciar sesión nuevamente.",
                "error": {
                    "error_code": "REFRESH_TOKEN_EXPIRED",
                    "details": "El refresh token no es válido o ya expiró. Solicite un nuevo inicio de sesión."
                }
            })
        ahora = datetime.now(timezone.utc)
        if sesion.fecha_expiracion_refresh < ahora:
            raise HTTPException(status_code=401, detail={
                "success": False,
                "statusCode": 401,
                "message": "El refresh token ha expirado. Debe iniciar sesión nuevamente.",
                "error": {
                    "error_code": "REFRESH_TOKEN_EXPIRED",
                    "details": "El refresh token no es válido o ya expiró. Solicite un nuevo inicio de sesión."
                }
            })
        fecha_exp_access = ahora + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        nuevo_access_token = jwt.encode({"sub": str(sesion.usuario_id), "exp": fecha_exp_access}, SECRET_KEY, algorithm=ALGORITHM)
        self.repo.actualizar_access_token(sesion.id, nuevo_access_token, fecha_exp_access)

        return {
            "success": True,
            "statusCode": 200,
            "message": "Token renovado correctamente",
            "data": {
                "accessToken": nuevo_access_token,
                "expiresIn": 3600
            }
        }