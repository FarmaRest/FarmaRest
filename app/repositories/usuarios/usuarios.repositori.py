# ─────────────────────────────────────────────────────────────────────────────
# CAPA: REPOSITORY — Módulo de Usuarios
# Responsabilidad: Es el ÚNICO lugar de todo el proyecto donde se hacen
# consultas a la base de datos. Recibe objetos Python y ejecuta las operaciones
# SQL a través de SQLAlchemy. Ninguna otra capa toca la BD directamente.
# ─────────────────────────────────────────────────────────────────────────────

from sqlalchemy.orm import Session
from app.domain.usuarios import Usuario, Direccion, HistorialCorreo


class UsuarioRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def buscar_por_correo(self, correo: str):
        return self.db.query(Usuario).filter(Usuario.correo == correo).first()

    def buscar_por_id(self, usuario_id: str):
        return self.db.query(Usuario).filter(Usuario.id == usuario_id).first()

    def guardar(self, usuario: Usuario):
        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def guardar_direcciones(self, direcciones: list[Direccion]):
        for direccion in direcciones:
            self.db.add(direccion)
        self.db.commit()

    def actualizar(self, usuario: Usuario, campos: dict) -> Usuario:
        for campo, valor in campos.items():
            setattr(usuario, campo, valor)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def eliminar(self, usuario: Usuario) -> None:
        self.db.delete(usuario)
        self.db.commit()

    def tiene_pedidos(self, usuario_id: str) -> bool:
        return False

    def actualizar_estado(self, usuario: Usuario, nuevo_estado: str) -> Usuario:
        usuario.estado = nuevo_estado
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def buscar_activos_sin_pedidos_desde(self, fecha_limite) -> list[Usuario]:
        return (
            self.db.query(Usuario)
            .filter(
                Usuario.estado == "activo",
                Usuario.fecha_registro <= fecha_limite,
            )
            .all()
        )

    def actualizar_contrasena(self, usuario, nuevo_hash: str, fecha_cambio) -> Usuario:
        usuario.hash_contrasena = nuevo_hash
        usuario.fecha_cambio_contrasena = fecha_cambio
        self.db.commit()
        self.db.refresh(usuario)
        return usuario


class DireccionRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def buscar_por_usuario(self, usuario_id: str) -> list[Direccion]:
        return self.db.query(Direccion).filter(Direccion.usuario_id == usuario_id).all()

    def buscar_por_id_y_usuario(self, dir_id: str, usuario_id: str):
        return self.db.query(Direccion).filter(
            Direccion.id == dir_id,
            Direccion.usuario_id == usuario_id
        ).first()

    def desmarcar_principal(self, usuario_id: str) -> None:
        self.db.query(Direccion).filter(Direccion.usuario_id == usuario_id).update({"principal": False})
        self.db.commit()

    def guardar(self, direccion: Direccion) -> Direccion:
        self.db.add(direccion)
        self.db.commit()
        self.db.refresh(direccion)
        return direccion

    def actualizar(self, direccion: Direccion, campos: dict) -> Direccion:
        for campo, valor in campos.items():
            setattr(direccion, campo, valor)
        self.db.commit()
        self.db.refresh(direccion)
        return direccion

    def eliminar(self, direccion: Direccion) -> None:
        self.db.delete(direccion)
        self.db.commit()


class HistorialCorreoRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def guardar(self, historial: HistorialCorreo) -> HistorialCorreo:
        self.db.add(historial)
        self.db.commit()
        self.db.refresh(historial)
        return historial

    def ultimo_cambio(self, usuario_id: str):
        return (
            self.db.query(HistorialCorreo)
            .filter(HistorialCorreo.usuario_id == usuario_id)
            .order_by(HistorialCorreo.fecha_cambio.desc())
            .first()
        )