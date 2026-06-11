# ─────────────────────────────────────────────────────────────────────────────
# CAPA: API — Módulo de Usuarios
# Responsabilidad: Expone los endpoints HTTP del módulo. Valida que el JSON
# recibido tenga el formato correcto usando schemas de Pydantic, luego delega
# al servicio correspondiente y retorna la respuesta estructurada.
# No contiene lógica de negocio ni accede a la BD directamente.
# ─────────────────────────────────────────────────────────────────────────────

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.usuarios import UsuarioService, DireccionService

# Prefijo base de todas las rutas de este módulo: /api/v1/usuarios
router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


# ─── Schemas de entrada y salida ─────────────────────────────────────────────
# Los schemas de Pydantic validan automáticamente el JSON que llega en el body.
# Si algún campo no cumple el tipo o la validación, FastAPI retorna 422 solo.

class DireccionIn(BaseModel):
    """Schema para recibir una dirección en el body de la petición."""
    direccion: str
    departamento: str
    ciudad: str
    principal: bool = False  # Por defecto no es la principal


class UsuarioIn(BaseModel):
    """Schema para registrar un nuevo usuario. Valida todos los campos del body."""
    primer_nombre: str
    segundo_nombre: Optional[str] = None      # Opcional
    primer_apellido: str
    segundo_apellido: Optional[str] = None    # Opcional
    cedula: str
    correo: EmailStr                          # Pydantic valida el formato del correo
    telefono: Optional[str] = None            # Opcional
    contrasena: str
    rol: Optional[str] = "cliente"            # Por defecto cliente
    direcciones: Optional[list[DireccionIn]] = []

    @field_validator("contrasena")
    @classmethod
    def validar_contrasena(cls, v):
        """Valida que la contraseña cumpla las reglas de seguridad mínimas."""
        if len(v) < 8:
            raise ValueError("La contraseña debe tener mínimo 8 caracteres")
        if not any(c.isupper() for c in v):
            raise ValueError("La contraseña debe tener al menos una mayúscula")
        if not any(c.isdigit() for c in v):
            raise ValueError("La contraseña debe tener al menos un número")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("La contraseña debe tener al menos un carácter especial")
        return v


class UsuarioUpdate(BaseModel):
    """Schema para actualizar un usuario. Todos los campos son opcionales —
    solo se actualiza lo que se envíe en el body."""
    primer_nombre: Optional[str] = None
    segundo_nombre: Optional[str] = None
    primer_apellido: Optional[str] = None
    segundo_apellido: Optional[str] = None
    telefono: Optional[str] = None
    contrasena: Optional[str] = None

    @field_validator("contrasena", mode="before")
    @classmethod
    def validar_contrasena(cls, v):
        """Valida la contraseña solo si se envía en el body."""
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError("La contraseña debe tener mínimo 8 caracteres")
        if not any(c.isupper() for c in v):
            raise ValueError("La contraseña debe tener al menos una mayúscula")
        if not any(c.isdigit() for c in v):
            raise ValueError("La contraseña debe tener al menos un número")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("La contraseña debe tener al menos un carácter especial")
        return v


# ─── Helpers de respuesta ─────────────────────────────────────────────────────
# Estas funciones estandarizan el formato de todas las respuestas del módulo

def _formato_respuesta(codigo: int, mensaje: str, data=None):
    """Estructura estándar para respuestas exitosas."""
    return {"success": True, "statusCode": codigo, "message": mensaje, "data": data}


def _formato_error(codigo: int, mensaje: str, error_code: str, detalle: str):
    """Estructura estándar para respuestas de error."""
    return {"success": False, "statusCode": codigo, "message": mensaje,
            "error": {"error_code": error_code, "details": detalle}}


# ─── HU-USR-01: Registro de usuario ──────────────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
def registrar_usuario(body: UsuarioIn, db: Session = Depends(get_db)):
    """
    Registra un nuevo usuario en el sistema.
    - Pydantic valida el body automáticamente antes de entrar aquí
    - El servicio verifica el correo duplicado y cifra la contraseña
    - Retorna 201 con los datos básicos del usuario (sin contraseña)
    """
    try:
        service = UsuarioService(db)
        usuario = service.registrar_usuario(body.model_dump())
        data = {
            "id": str(usuario.id),
            "primer_nombre": usuario.primer_nombre,
            "primer_apellido": usuario.primer_apellido,
            "correo": usuario.correo,
            "rol": usuario.rol,
            "fecha_registro": usuario.fecha_registro.isoformat(),
        }
        return _formato_respuesta(201, "Usuario registrado correctamente", data)
    except ValueError as e:
        if "EMAIL_ALREADY_EXISTS" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_formato_error(409, "Correo ya registrado", "EMAIL_ALREADY_EXISTS",
                                      f"El correo {body.correo} ya está asociado a una cuenta")
            )
        if "CEDULA_ALREADY_EXISTS" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_formato_error(409, "Cédula ya registrada", "CEDULA_ALREADY_EXISTS",
                                      f"La cédula {body.cedula} ya está asociada a una cuenta")
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=_formato_error(400, "Datos inválidos", "VALIDATION_ERROR", str(e)))


# ─── HU-USR-02: Actualización de usuario ─────────────────────────────────────

@router.put("/{usuario_id}", status_code=status.HTTP_200_OK)
def actualizar_usuario(
    usuario_id: str,
    body: UsuarioUpdate,
    db: Session = Depends(get_db),
    usuario_actual=Depends(get_current_user),
):
    """
    Actualiza los datos personales de un usuario.
    Requiere token JWT válido. Un cliente solo puede modificar su propio perfil.
    """
    try:
        service = UsuarioService(db)
        usuario = service.actualizar_usuario(usuario_id, body.model_dump(exclude_none=True), str(usuario_actual.id), usuario_actual.rol)
        data = {
            "id": str(usuario.id),
            "primer_nombre": usuario.primer_nombre,
            "segundo_nombre": usuario.segundo_nombre,
            "primer_apellido": usuario.primer_apellido,
            "segundo_apellido": usuario.segundo_apellido,
            "correo": usuario.correo,
            "telefono": usuario.telefono,
            "rol": usuario.rol,
            "estado": usuario.estado,
        }
        return _formato_respuesta(200, "Usuario actualizado correctamente", data)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_formato_error(403, "Acceso denegado", "FORBIDDEN",
                                  "No tiene permisos para modificar el perfil de otro usuario")
        )
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_formato_error(404, "Usuario no encontrado", "USER_NOT_FOUND",
                                  "No existe un usuario con el ID proporcionado")
        )
    except ValueError as e:
        if "PASSWORD_REUSE_NOT_ALLOWED" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_formato_error(400, "No puede reutilizar una contraseña anterior",
                                      "PASSWORD_REUSE_NOT_ALLOWED",
                                      "La contraseña ingresada ya fue utilizada anteriormente")
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=_formato_error(400, "Datos inválidos", "VALIDATION_ERROR", str(e)))


# ─── HU-USR-02: Eliminación de usuario ───────────────────────────────────────

@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_usuario(
    usuario_id: str,
    db: Session = Depends(get_db),
    usuario_actual=Depends(get_current_user),
):
    """
    Elimina un usuario. Solo lo puede hacer un administrador.
    No se puede eliminar si tiene pedidos asociados.
    Retorna 204 (sin contenido en el body).
    """
    try:
        service = UsuarioService(db)
        service.eliminar_usuario(usuario_id, usuario_actual.rol)
        return None
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_formato_error(403, "Acceso denegado", "FORBIDDEN",
                                  "Solo un administrador puede eliminar cuentas")
        )
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_formato_error(404, "Usuario no encontrado", "USER_NOT_FOUND",
                                  "No existe un usuario con el ID proporcionado")
        )
    except ValueError as e:
        if "USER_HAS_ORDERS" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_formato_error(409, "No se puede eliminar el usuario porque tiene pedidos asociados",
                                      "USER_HAS_ORDERS",
                                      f"El usuario {usuario_id} tiene pedidos registrados en el sistema")
            )


# ─── HU-USR-03: Gestión de direcciones ───────────────────────────────────────

class DireccionIn(BaseModel):
    """Schema para agregar una nueva dirección."""
    direccion: str
    departamento: str
    ciudad: str
    principal: bool = False


class DireccionUpdate(BaseModel):
    """Schema para actualizar una dirección. Todos los campos son opcionales."""
    direccion: Optional[str] = None
    departamento: Optional[str] = None
    ciudad: Optional[str] = None
    principal: Optional[bool] = None


def _dir_dict(d) -> dict:
    """Convierte un objeto Direccion a diccionario para la respuesta."""
    return {
        "id": str(d.id),
        "usuario_id": str(d.usuario_id),
        "direccion": d.direccion,
        "departamento": d.departamento,
        "ciudad": d.ciudad,
        "principal": d.principal,
    }


@router.post("/{usuario_id}/direcciones", status_code=status.HTTP_201_CREATED)
def agregar_direccion(usuario_id: str, body: DireccionIn, db: Session = Depends(get_db)):
    """
    Agrega una nueva dirección de entrega al usuario.
    Si se marca como principal, desactiva automáticamente las demás.
    """
    try:
        service = DireccionService(db)
        dir_nueva = service.agregar(usuario_id, body.model_dump())
        return _formato_respuesta(201, "Dirección agregada correctamente", _dir_dict(dir_nueva))
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=_formato_error(404, "Usuario no encontrado", "USER_NOT_FOUND",
                                                  "No existe un usuario con el ID proporcionado"))


@router.get("/{usuario_id}/direcciones", status_code=status.HTTP_200_OK)
def consultar_direcciones(
    usuario_id: str,
    db: Session = Depends(get_db),
    solicitante_id: Optional[str] = None,
    solicitante_rol: Optional[str] = "cliente",
):
    """
    Retorna todas las direcciones de entrega registradas del usuario.
    Un cliente solo puede consultar sus propias direcciones; un admin puede consultar cualquiera.
    Pendiente: reemplazar solicitante_id y solicitante_rol por JWT en HU de autenticación.
    """
    try:
        sid = solicitante_id if solicitante_id else usuario_id
        if solicitante_rol == "cliente" and sid != usuario_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=_formato_error(403, "Acceso denegado", "FORBIDDEN",
                                      "No tiene permisos para consultar las direcciones de otro usuario")
            )
        service = DireccionService(db)
        dirs = service.consultar(usuario_id)
        return _formato_respuesta(200, "Direcciones obtenidas correctamente", [_dir_dict(d) for d in dirs])
    except HTTPException:
        raise
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=_formato_error(404, "Usuario no encontrado", "USER_NOT_FOUND",
                                                  "No existe un usuario con el ID proporcionado"))


@router.put("/{usuario_id}/direcciones/{dir_id}", status_code=status.HTTP_200_OK)
def actualizar_direccion(usuario_id: str, dir_id: str, body: DireccionUpdate, db: Session = Depends(get_db)):
    """
    Actualiza una dirección existente del usuario.
    Verifica que la dirección pertenezca al usuario antes de modificarla.
    """
    try:
        service = DireccionService(db)
        dir_act = service.actualizar(usuario_id, dir_id, body.model_dump(exclude_none=True))
        return _formato_respuesta(200, "Dirección actualizada correctamente", _dir_dict(dir_act))
    except LookupError as e:
        code = "ADDRESS_NOT_FOUND" if "ADDRESS" in str(e) else "USER_NOT_FOUND"
        msg = "Dirección no encontrada" if "ADDRESS" in str(e) else "Usuario no encontrado"
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=_formato_error(404, msg, code,
                                                  "No existe una dirección con el ID proporcionado para este usuario"))


@router.delete("/{usuario_id}/direcciones/{dir_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_direccion(usuario_id: str, dir_id: str, db: Session = Depends(get_db)):
    """
    Elimina una dirección del usuario.
    Verifica que la dirección pertenezca al usuario antes de eliminarla.
    Retorna 204 (sin contenido en el body).
    """
    try:
        service = DireccionService(db)
        service.eliminar(usuario_id, dir_id)
        return None
    except LookupError as e:
        code = "ADDRESS_NOT_FOUND" if "ADDRESS" in str(e) else "USER_NOT_FOUND"
        msg = "Dirección no encontrada" if "ADDRESS" in str(e) else "Usuario no encontrado"
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=_formato_error(404, msg, code,
                                                  "No existe una dirección con el ID proporcionado para este usuario"))


# ─── HU-USR-04: Cambio de estado ─────────────────────────────────────────────

class EstadoUpdate(BaseModel):
    """Schema para cambiar el estado de un usuario."""
    estado: str  # Solo acepta: 'activo' o 'inactivo'


@router.patch("/{usuario_id}/estado", status_code=status.HTTP_200_OK)
def actualizar_estado(
    usuario_id: str,
    body: EstadoUpdate,
    db: Session = Depends(get_db),
    solicitante_rol: Optional[str] = "cliente",
):
    """
    Cambia el estado de un usuario entre activo e inactivo.
    Solo puede hacerlo un administrador.
    Se usa para reactivar cuentas inactivadas por el cron job.
    Pendiente: reemplazar solicitante_rol por JWT en HU de autenticación.
    """
    try:
        service = UsuarioService(db)
        usuario = service.actualizar_estado(usuario_id, body.estado, solicitante_rol)
        return _formato_respuesta(200, "Estado del usuario actualizado correctamente", {
            "id": str(usuario.id),
            "primer_nombre": usuario.primer_nombre,
            "primer_apellido": usuario.primer_apellido,
            "correo": usuario.correo,
            "estado": usuario.estado,
            "fecha_actualizacion": datetime.now(timezone.utc).isoformat(),
        })
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_formato_error(403, "Acceso denegado", "FORBIDDEN",
                                  "Solo un administrador puede cambiar el estado de una cuenta de usuario")
        )
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_formato_error(404, "Usuario no encontrado", "USER_NOT_FOUND",
                                  "No existe un usuario con el ID proporcionado")
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_formato_error(400, "El estado proporcionado no es válido", "INVALID_STATUS",
                                  "Los valores válidos para el campo estado son: activo, inactivo")
        )


# ─── HU-USR-03: Cambio de correo ─────────────────────────────────────────────

class CorreoUpdate(BaseModel):
    """Schema para cambiar el correo electrónico del usuario."""
    correo: EmailStr  # Pydantic valida el formato del correo automáticamente


@router.patch("/{usuario_id}/correo", status_code=status.HTTP_200_OK)
def cambiar_correo(usuario_id: str, body: CorreoUpdate, db: Session = Depends(get_db)):
    """
    Cambia el correo electrónico del usuario.
    Valida la restricción de un cambio cada 6 meses consultando historial_correos.
    Guarda el correo anterior en historial antes de actualizar.
    """
    try:
        service = UsuarioService(db)
        usuario = service.cambiar_correo(usuario_id, body.correo, db)
        return _formato_respuesta(200, "Correo electrónico actualizado correctamente", {
            "id": str(usuario.id),
            "correo": usuario.correo,
            "fecha_actualizacion": datetime.now(timezone.utc).isoformat(),
        })
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=_formato_error(404, "Usuario no encontrado", "USER_NOT_FOUND",
                                                  "No existe un usuario con el ID proporcionado"))
    except ValueError as e:
        err = str(e)
        if "EMAIL_CHANGE_RESTRICTED" in err:
            # El servicio pasa la fecha del próximo cambio permitido después de los dos puntos
            fecha = err.split(":")[1]
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=_formato_error(409, "No puede cambiar su correo en este momento",
                                                      "EMAIL_CHANGE_RESTRICTED",
                                                      f"Solo se permite un cambio cada 6 meses. Próximo cambio: {fecha}"))
        if "EMAIL_ALREADY_EXISTS" in err:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=_formato_error(409, "El correo ya se encuentra registrado",
                                                      "EMAIL_ALREADY_EXISTS",
                                                      f"El correo {body.correo} ya está asociado a otra cuenta"))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=_formato_error(400, "Datos inválidos", "VALIDATION_ERROR", err))


# ─── HU-USR-01: Consulta de usuario ──────────────────────────────────────────

@router.get("/{usuario_id}", status_code=status.HTTP_200_OK)
def consultar_usuario(
    usuario_id: str,
    db: Session = Depends(get_db),
    usuario_actual=Depends(get_current_user),
):
    """
    Retorna el perfil completo del usuario incluyendo sus direcciones.
    Requiere token JWT válido en el header Authorization: Bearer <token>.
    Un cliente solo puede consultar su propio perfil; un admin puede consultar cualquiera.
    """
    try:
        service = UsuarioService(db)
        usuario = service.consultar_por_id(usuario_id, str(usuario_actual.id), usuario_actual.rol)
        data = {
            "id": str(usuario.id),
            "primer_nombre": usuario.primer_nombre,
            "segundo_nombre": usuario.segundo_nombre,
            "primer_apellido": usuario.primer_apellido,
            "segundo_apellido": usuario.segundo_apellido,
            "cedula": usuario.cedula,
            "correo": usuario.correo,
            "telefono": usuario.telefono,
            "rol": usuario.rol,
            "estado": usuario.estado,
            "fecha_registro": usuario.fecha_registro.isoformat(),
            # Se construye la lista de direcciones directamente desde la relación ORM
            "direcciones": [
                {
                    "id": str(d.id),
                    "direccion": d.direccion,
                    "departamento": d.departamento,
                    "ciudad": d.ciudad,
                    "principal": d.principal,
                }
                for d in usuario.direcciones
            ],
        }
        return _formato_respuesta(200, "Usuario encontrado", data)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_formato_error(403, "Acceso denegado", "FORBIDDEN",
                                  "No tiene permisos para consultar el perfil de otro usuario")
        )
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_formato_error(404, "Usuario no encontrado", "USER_NOT_FOUND",
                                  "No existe un usuario con el ID proporcionado")
        )
