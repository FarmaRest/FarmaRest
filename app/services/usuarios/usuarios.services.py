# ─────────────────────────────────────────────────────────────────────────────
# CAPA: SERVICE — Módulo de Usuarios
# Responsabilidad: Contiene toda la lógica de aplicación. Coordina entre la
# capa API y la capa Repository. Aquí se toman las decisiones del negocio:
# validar permisos, verificar reglas, orquestar operaciones.
# No escribe SQL ni responde HTTP — solo lógica pura.
# ─────────────────────────────────────────────────────────────────────────────

import uuid
import bcrypt
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.repositories.usuarios import UsuarioRepositorio, DireccionRepositorio, HistorialCorreoRepositorio
from app.domain.usuarios import Usuario, Direccion, HistorialCorreo


class UsuarioService:
    """
    Servicio principal del módulo de usuarios.
    Maneja el ciclo de vida completo: registro, consulta, actualización,
    eliminación, cambio de correo y cambio de estado.
    """

    def __init__(self, db: Session):
        # Se instancia el repositorio pasándole la sesión de BD
        self.repo = UsuarioRepositorio(db)

    def registrar_usuario(self, datos: dict) -> Usuario:
        """HU-USR-01: Registra un nuevo usuario en el sistema."""

        # Regla de negocio: el correo debe ser único en todo el sistema
        if self.repo.buscar_por_correo(datos["correo"]):
            raise ValueError("EMAIL_ALREADY_EXISTS")

        # Regla de negocio: la cédula debe ser única en todo el sistema
        if self.repo.buscar_por_cedula(datos["cedula"]):
            raise ValueError("CEDULA_ALREADY_EXISTS")

        # La contraseña nunca se guarda en texto plano — se cifra con bcrypt
        # bcrypt genera un salt aleatorio internamente cada vez, por eso es seguro
        hash_pw = bcrypt.hashpw(datos["contrasena"].encode(), bcrypt.gensalt()).decode()

        # Se construye el objeto Usuario con los datos recibidos
        nuevo_usuario = Usuario(
            primer_nombre=datos["primer_nombre"],
            segundo_nombre=datos.get("segundo_nombre"),       # Opcional
            primer_apellido=datos["primer_apellido"],
            segundo_apellido=datos.get("segundo_apellido"),   # Opcional
            cedula=datos["cedula"],
            correo=datos["correo"],
            hash_contrasena=hash_pw,
            telefono=datos.get("telefono"),                   # Opcional
            rol=datos.get("rol", "cliente"),                  # Por defecto: cliente
        )
        usuario_guardado = self.repo.guardar(nuevo_usuario)

        # Si se enviaron direcciones en el registro, se guardan asociadas al usuario
        if datos.get("direcciones"):
            direcciones = [
                Direccion(
                    usuario_id=usuario_guardado.id,
                    direccion=d["direccion"],
                    departamento=d["departamento"],
                    ciudad=d["ciudad"],
                    principal=d.get("principal", False),
                )
                for d in datos["direcciones"]
            ]
            self.repo.guardar_direcciones(direcciones)

        return usuario_guardado

    def consultar_por_id(self, usuario_id: str, solicitante_id: str, solicitante_rol: str) -> Usuario:
        """HU-USR-01: Consulta un usuario por su ID con validación de permisos."""

        # Regla: un cliente solo puede ver su propio perfil
        # Un admin puede ver cualquier perfil
        if solicitante_rol == "cliente" and solicitante_id != usuario_id:
            raise PermissionError("FORBIDDEN")

        usuario = self.repo.buscar_por_id(usuario_id)
        if not usuario:
            raise LookupError("USER_NOT_FOUND")

        return usuario

    def actualizar_usuario(self, usuario_id: str, datos: dict, solicitante_id: str, solicitante_rol: str) -> Usuario:
        """HU-USR-02: Actualiza datos personales del usuario."""

        # Regla: un cliente solo puede modificar su propio perfil
        if solicitante_rol == "cliente" and solicitante_id != usuario_id:
            raise PermissionError("FORBIDDEN")

        usuario = self.repo.buscar_por_id(usuario_id)
        if not usuario:
            raise LookupError("USER_NOT_FOUND")

        # Solo se actualizan los campos que llegaron en el body (los demás quedan igual)
        campos_a_actualizar = {}
        for campo in ("primer_nombre", "segundo_nombre", "primer_apellido", "segundo_apellido", "telefono"):
            if datos.get(campo) is not None:
                campos_a_actualizar[campo] = datos[campo]

        # Si se envía una nueva contraseña, se verifica que no sea igual a la actual
        if datos.get("contrasena"):
            nuevo_hash = bcrypt.hashpw(datos["contrasena"].encode(), bcrypt.gensalt())
            # checkpw compara la contraseña en texto plano con el hash almacenado
            if bcrypt.checkpw(datos["contrasena"].encode(), usuario.hash_contrasena.encode()):
                raise ValueError("PASSWORD_REUSE_NOT_ALLOWED")
            campos_a_actualizar["hash_contrasena"] = nuevo_hash.decode()

        return self.repo.actualizar(usuario, campos_a_actualizar)

    def eliminar_usuario(self, usuario_id: str, solicitante_rol: str) -> None:
        """HU-USR-02: Elimina un usuario del sistema. Solo lo puede hacer un admin."""

        # Regla: solo administradores pueden eliminar cuentas
        if solicitante_rol != "admin":
            raise PermissionError("FORBIDDEN")

        usuario = self.repo.buscar_por_id(usuario_id)
        if not usuario:
            raise LookupError("USER_NOT_FOUND")

        # Regla: no se puede eliminar un usuario que tenga pedidos registrados
        if self.repo.tiene_pedidos(usuario_id):
            raise ValueError("USER_HAS_ORDERS")

        # El CASCADE en el domain elimina automáticamente direcciones e historial
        self.repo.eliminar(usuario)

    def actualizar_estado(self, usuario_id: str, nuevo_estado: str, solicitante_rol: str) -> Usuario:
        """HU-USR-04: Cambia el estado de un usuario entre activo e inactivo. Solo admin."""

        if solicitante_rol != "admin":
            raise PermissionError("FORBIDDEN")

        # Solo se aceptan estos dos valores de estado
        if nuevo_estado not in ("activo", "inactivo"):
            raise ValueError("INVALID_STATUS")

        usuario = self.repo.buscar_por_id(usuario_id)
        if not usuario:
            raise LookupError("USER_NOT_FOUND")

        return self.repo.actualizar_estado(usuario, nuevo_estado)

    def cambiar_correo(self, usuario_id: str, nuevo_correo: str, db: Session) -> Usuario:
        """HU-USR-03: Cambia el correo del usuario respetando la restricción de 6 meses."""

        usuario = self.repo.buscar_por_id(usuario_id)
        if not usuario:
            raise LookupError("USER_NOT_FOUND")

        # Regla: el nuevo correo no puede estar en uso por otro usuario
        if self.repo.buscar_por_correo(nuevo_correo):
            raise ValueError("EMAIL_ALREADY_EXISTS")

        historial_repo = HistorialCorreoRepositorio(db)
        ultimo = historial_repo.ultimo_cambio(usuario_id)

        # Regla: solo se permite un cambio de correo cada 6 meses (182 días)
        if ultimo:
            seis_meses = timedelta(days=182)
            proximo_cambio = ultimo.fecha_cambio + seis_meses
            if datetime.now(timezone.utc) < proximo_cambio:
                raise ValueError(f"EMAIL_CHANGE_RESTRICTED:{proximo_cambio.date().isoformat()}")

        # Antes de cambiar, se guarda el correo anterior en el historial
        historial_repo.guardar(HistorialCorreo(
            usuario_id=usuario.id,
            correo_anterior=usuario.correo,
        ))

        return self.repo.actualizar(usuario, {"correo": nuevo_correo})


class InactivacionService:
    """
    HU-USR-04: Servicio de inactivación automática por inactividad.
    Es ejecutado por el cron job diario definido en app/core/cron.py.
    Detecta usuarios activos sin pedidos en los últimos 6 meses y los inactiva.
    """

    def __init__(self, db: Session):
        self.repo = UsuarioRepositorio(db)

    def ejecutar(self) -> int:
        """
        Ejecuta el proceso de inactivación.
        Retorna el número de usuarios que fueron inactivados.
        """
        # Fecha límite: hoy menos 6 meses. Usuarios registrados antes de esta
        # fecha y sin pedidos recientes serán inactivados
        fecha_limite = datetime.now(timezone.utc) - timedelta(days=182)
        usuarios = self.repo.buscar_activos_sin_pedidos_desde(fecha_limite)

        inactivados = 0
        for usuario in usuarios:
            try:
                self.repo.actualizar_estado(usuario, "inactivo")
                inactivados += 1
            except Exception as e:
                # Si falla un usuario, se registra el error y se continúa con los demás
                import logging
                logging.error(f"[CRON] Error inactivando usuario {usuario.id}: {e}")

        return inactivados


class DireccionService:
    """
    HU-USR-03: Maneja el CRUD completo de direcciones de entrega del usuario.
    Garantiza que solo exista una dirección principal por usuario a la vez.
    """

    def __init__(self, db: Session):
        self.repo = DireccionRepositorio(db)
        self.usuario_repo = UsuarioRepositorio(db)

    def _verificar_usuario(self, usuario_id: str):
        """Verifica que el usuario exista antes de operar sobre sus direcciones."""
        if not self.usuario_repo.buscar_por_id(usuario_id):
            raise LookupError("USER_NOT_FOUND")

    def agregar(self, usuario_id: str, datos: dict) -> Direccion:
        """Agrega una nueva dirección al usuario."""
        self._verificar_usuario(usuario_id)

        # Si la nueva dirección es principal, primero se desmarcan todas las demás
        # para garantizar que solo exista una principal por usuario
        if datos.get("principal"):
            self.repo.desmarcar_principal(usuario_id)

        nueva = Direccion(
            usuario_id=uuid.UUID(usuario_id),
            direccion=datos["direccion"],
            departamento=datos["departamento"],
            ciudad=datos["ciudad"],
            principal=datos.get("principal", False),
        )
        return self.repo.guardar(nueva)

    def consultar(self, usuario_id: str) -> list[Direccion]:
        """Retorna todas las direcciones registradas del usuario."""
        self._verificar_usuario(usuario_id)
        return self.repo.buscar_por_usuario(usuario_id)

    def actualizar(self, usuario_id: str, dir_id: str, datos: dict) -> Direccion:
        """Actualiza una dirección existente verificando que pertenezca al usuario."""
        self._verificar_usuario(usuario_id)

        # Busca la dirección verificando que sea del usuario — evita acceso cruzado
        direccion = self.repo.buscar_por_id_y_usuario(dir_id, usuario_id)
        if not direccion:
            raise LookupError("ADDRESS_NOT_FOUND")

        # Si se marca como principal, se desmarcan las demás primero
        if datos.get("principal"):
            self.repo.desmarcar_principal(usuario_id)

        return self.repo.actualizar(direccion, datos)

    def eliminar(self, usuario_id: str, dir_id: str) -> None:
        """Elimina una dirección verificando que pertenezca al usuario."""
        self._verificar_usuario(usuario_id)

        direccion = self.repo.buscar_por_id_y_usuario(dir_id, usuario_id)
        if not direccion:
            raise LookupError("ADDRESS_NOT_FOUND")

        self.repo.eliminar(direccion)
