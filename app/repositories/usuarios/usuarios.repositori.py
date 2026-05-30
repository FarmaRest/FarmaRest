# ─────────────────────────────────────────────────────────────────────────────
# CAPA: REPOSITORY — Módulo de Usuarios
# Responsabilidad: Es el ÚNICO lugar de todo el proyecto donde se hacen
# consultas a la base de datos. Recibe objetos Python y ejecuta las operaciones
# SQL a través de SQLAlchemy. Ninguna otra capa toca la BD directamente.
# ─────────────────────────────────────────────────────────────────────────────

from sqlalchemy.orm import Session
from app.domain.usuarios import Usuario, Direccion, HistorialCorreo


class UsuarioRepositorio:
    """
    Maneja todas las operaciones de base de datos para la tabla 'usuarios'.
    Recibe la sesión de BD (db) al instanciarse, que es la conexión activa
    inyectada por FastAPI a través de get_db().
    """

    def __init__(self, db: Session):
        # db es la sesión activa de SQLAlchemy — la conexión a PostgreSQL
        self.db = db

    def buscar_por_correo(self, correo: str):
        # Busca un usuario por correo. Se usa para verificar duplicados antes de registrar
        # y para validar credenciales en el login
        return self.db.query(Usuario).filter(Usuario.correo == correo).first()

    def buscar_por_id(self, usuario_id: str):
        # Busca un usuario por su UUID. Retorna None si no existe
        return self.db.query(Usuario).filter(Usuario.id == usuario_id).first()

    def guardar(self, usuario: Usuario):
        # Inserta el nuevo usuario en la BD, confirma la transacción y
        # refresca el objeto para obtener los valores generados por la BD (ej: fecha_registro)
        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def guardar_direcciones(self, direcciones: list[Direccion]):
        # Inserta todas las direcciones de un usuario de una sola vez.
        # Se hace un solo commit al final para que sea atómico
        for direccion in direcciones:
            self.db.add(direccion)
        self.db.commit()

    def actualizar(self, usuario: Usuario, campos: dict) -> Usuario:
        # Actualiza solo los campos que se pasen en el diccionario.
        # setattr aplica el cambio al objeto en memoria, commit lo persiste en la BD
        for campo, valor in campos.items():
            setattr(usuario, campo, valor)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def eliminar(self, usuario: Usuario) -> None:
        # Elimina el usuario. Por el CASCADE definido en el domain,
        # sus direcciones e historial_correos se eliminan automáticamente
        self.db.delete(usuario)
        self.db.commit()

    def tiene_pedidos(self, usuario_id: str) -> bool:
        # Verifica si el usuario tiene pedidos antes de permitir su eliminación.
        # Pendiente: cuando el módulo de pedidos esté implementado se agrega el join
        return False

    def actualizar_estado(self, usuario: Usuario, nuevo_estado: str) -> Usuario:
        # Cambia el estado del usuario entre 'activo' e 'inactivo'.
        # Lo usa tanto el endpoint manual (admin) como el cron de inactivación
        usuario.estado = nuevo_estado
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def buscar_activos_sin_pedidos_desde(self, fecha_limite) -> list[Usuario]:
        # Retorna usuarios activos registrados antes de fecha_limite.
        # El cron de HU-USR-04 usa esto para detectar usuarios inactivos.
        # Pendiente: agregar filtro de pedidos cuando ese módulo esté listo
        return (
            self.db.query(Usuario)
            .filter(
                Usuario.estado == "activo",
                Usuario.fecha_registro <= fecha_limite,
            )
            .all()
        )


class DireccionRepositorio:
    """
    Maneja todas las operaciones de base de datos para la tabla 'direcciones'.
    """

    def __init__(self, db: Session):
        self.db = db

    def buscar_por_usuario(self, usuario_id: str) -> list[Direccion]:
        # Retorna todas las direcciones de un usuario ordenadas por la BD
        return self.db.query(Direccion).filter(Direccion.usuario_id == usuario_id).all()

    def buscar_por_id_y_usuario(self, dir_id: str, usuario_id: str):
        # Busca una dirección específica verificando que pertenezca al usuario correcto.
        # Esto evita que un usuario pueda modificar direcciones ajenas
        return self.db.query(Direccion).filter(
            Direccion.id == dir_id,
            Direccion.usuario_id == usuario_id
        ).first()

    def desmarcar_principal(self, usuario_id: str) -> None:
        # Pone principal=False en TODAS las direcciones del usuario.
        # Se llama antes de marcar una nueva como principal para garantizar
        # que solo exista una dirección principal por usuario a la vez
        self.db.query(Direccion).filter(Direccion.usuario_id == usuario_id).update({"principal": False})
        self.db.commit()

    def guardar(self, direccion: Direccion) -> Direccion:
        # Inserta una nueva dirección en la BD
        self.db.add(direccion)
        self.db.commit()
        self.db.refresh(direccion)
        return direccion

    def actualizar(self, direccion: Direccion, campos: dict) -> Direccion:
        # Actualiza solo los campos enviados en el diccionario
        for campo, valor in campos.items():
            setattr(direccion, campo, valor)
        self.db.commit()
        self.db.refresh(direccion)
        return direccion

    def eliminar(self, direccion: Direccion) -> None:
        # Elimina la dirección de la BD
        self.db.delete(direccion)
        self.db.commit()


class HistorialCorreoRepositorio:
    """
    Maneja todas las operaciones de base de datos para la tabla 'historial_correos'.
    Se usa para registrar cada cambio de correo y validar la restricción de 6 meses.
    """

    def __init__(self, db: Session):
        self.db = db

    def guardar(self, historial: HistorialCorreo) -> HistorialCorreo:
        # Guarda el correo anterior antes de que se actualice el nuevo.
        # Esto crea la trazabilidad del historial de correos del usuario
        self.db.add(historial)
        self.db.commit()
        self.db.refresh(historial)
        return historial

    def ultimo_cambio(self, usuario_id: str):
        # Retorna el cambio de correo más reciente del usuario.
        # Se ordena desc para traer el más nuevo primero.
        # Si retorna None, el usuario nunca ha cambiado su correo
        return (
            self.db.query(HistorialCorreo)
            .filter(HistorialCorreo.usuario_id == usuario_id)
            .order_by(HistorialCorreo.fecha_cambio.desc())
            .first()
        )
