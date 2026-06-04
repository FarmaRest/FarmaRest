from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from jose import jwt
from fastapi import HTTPException
import bcrypt
import os
import importlib.util
import uuid
import re

# Cargar repositorio de autenticacion
_path_repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "repositories", "autenticacion", "autenticacion.repositori.py"))
_spec_repo = importlib.util.spec_from_file_location("autenticacion_repositori", _path_repo)
_mod_repo = importlib.util.module_from_spec(_spec_repo)
_spec_repo.loader.exec_module(_mod_repo)
AutenticacionRepositorio = _mod_repo.AutenticacionRepositorio

# Cargar repositorio de contrasenas
_path_cont = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "repositories", "autenticacion", "contrasena.repositori.py"))
_spec_cont = importlib.util.spec_from_file_location("contrasena_repositori", _path_cont)
_mod_cont = importlib.util.module_from_spec(_spec_cont)
_spec_cont.loader.exec_module(_mod_cont)
HistorialContrasenaRepositorio = _mod_cont.HistorialContrasenaRepositorio

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
PASSWORD_EXPIRE_DAYS = 45
PASSWORD_WARNING_DAYS = 5


def validar_contrasena_fuerte(contrasena: str) -> bool:
    if len(contrasena) < 8:
        return False
    if not re.search(r'[A-Z]', contrasena):
        return False
    if not re.search(r'[0-9]', contrasena):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', contrasena):
        return False
    return True


class AutenticacionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AutenticacionRepositorio(db)
        self.usuario_repo = UsuarioRepositorio(db)
        self.historial_repo = HistorialContrasenaRepositorio(db)

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

        advertencia = None
        if usuario.rol == "administrador" and usuario.fecha_cambio_contrasena:
            ahora = datetime.now(timezone.utc)
            dias_desde_cambio = (ahora - usuario.fecha_cambio_contrasena).days
            dias_restantes = PASSWORD_EXPIRE_DAYS - dias_desde_cambio
            if dias_desde_cambio > PASSWORD_EXPIRE_DAYS:
                raise HTTPException(status_code=403, detail={
                    "success": False,
                    "statusCode": 403,
                    "message": "Tu contraseña ha vencido. Debes cambiarla para continuar.",
                    "error": {
                        "error_code": "PASSWORD_EXPIRED",
                        "details": "Las contraseñas de administrador deben cambiarse cada 45 días."
                    }
                })
            elif dias_restantes <= PASSWORD_WARNING_DAYS:
                advertencia = f"Tu contraseña vence en {dias_restantes} días. Cámbiala pronto para evitar bloqueos."

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

        respuesta = {
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
        if advertencia:
            respuesta["data"]["advertencia"] = advertencia
        return respuesta

    def logout(self, refresh_token: str) -> dict:
        sesion = self.repo.buscar_por_refresh_token(refresh_token)
        if not sesion:
            raise HTTPException(status_code=401, detail={
                "success": False,
                "statusCode": 401,
                "message": "Token inválido o expirado",
                "error": {"error_code": "INVALID_TOKEN"}
            })
        self.repo.desactivar_sesion(sesion.id)
        return {"success": True, "statusCode": 200, "message": "Sesión cerrada correctamente", "data": None}

    def refresh_token(self, refresh_token: str) -> dict:
        sesion = self.repo.buscar_por_refresh_token(refresh_token)
        if not sesion:
            raise HTTPException(status_code=401, detail={
                "success": False,
                "statusCode": 401,
                "message": "El refresh token ha expirado.",
                "error": {"error_code": "REFRESH_TOKEN_EXPIRED"}
            })
        ahora = datetime.now(timezone.utc)
        if sesion.fecha_expiracion_refresh < ahora:
            raise HTTPException(status_code=401, detail={
                "success": False,
                "statusCode": 401,
                "message": "El refresh token ha expirado.",
                "error": {"error_code": "REFRESH_TOKEN_EXPIRED"}
            })
        fecha_exp_access = ahora + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        nuevo_access_token = jwt.encode({"sub": str(sesion.usuario_id), "exp": fecha_exp_access}, SECRET_KEY, algorithm=ALGORITHM)
        self.repo.actualizar_access_token(sesion.id, nuevo_access_token, fecha_exp_access)
        return {"success": True, "statusCode": 200, "message": "Token renovado correctamente", "data": {"accessToken": nuevo_access_token, "expiresIn": 3600}}

    def cambiar_contrasena(self, correo: str, contrasena_actual: str, contrasena_nueva: str) -> dict:
        usuario = self.usuario_repo.buscar_por_correo(correo)
        if not usuario:
            raise HTTPException(status_code=404, detail={"success": False, "statusCode": 404, "message": "Usuario no encontrado"})
        if not bcrypt.checkpw(contrasena_actual.encode("utf-8"), usuario.hash_contrasena.encode("utf-8")):
            raise HTTPException(status_code=401, detail={"success": False, "statusCode": 401, "message": "La contraseña actual es incorrecta", "error": {"error_code": "INVALID_CURRENT_PASSWORD"}})
        if not validar_contrasena_fuerte(contrasena_nueva):
            raise HTTPException(status_code=400, detail={"success": False, "statusCode": 400, "message": "La nueva contraseña no cumple los requisitos mínimos de seguridad", "error": {"error_code": "WEAK_PASSWORD"}})
        historiales = self.historial_repo.buscar_por_usuario_id(usuario.id)
        for h in historiales:
            if bcrypt.checkpw(contrasena_nueva.encode("utf-8"), h.hash_contrasena.encode("utf-8")):
                raise HTTPException(status_code=400, detail={"success": False, "statusCode": 400, "message": "No puede reutilizar una contraseña anterior", "error": {"error_code": "PASSWORD_REUSE_NOT_ALLOWED"}})
        hash_anterior = usuario.hash_contrasena
        nuevo_hash = bcrypt.hashpw(contrasena_nueva.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        ahora = datetime.now(timezone.utc)
        self.usuario_repo.actualizar_contrasena(usuario, nuevo_hash, ahora)
        self.historial_repo.guardar(usuario.id, hash_anterior)
        return {"success": True, "statusCode": 200, "message": "Contraseña actualizada correctamente.", "data": {"usuarioId": str(usuario.id), "correo": usuario.correo, "fechaCambioContrasena": ahora.isoformat()}}