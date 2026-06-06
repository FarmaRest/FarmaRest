from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.domain.autenticacion import Sesion


class AutenticacionRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def guardar(self, sesion: Sesion) -> Sesion:
        self.db.add(sesion)
        self.db.commit()
        self.db.refresh(sesion)
        return sesion

    def buscar_por_refresh_token(self, refresh_token: str):
        return self.db.query(Sesion).filter(
            Sesion.refresh_token == refresh_token,
            Sesion.activa == True
        ).first()

    def buscar_por_access_token(self, access_token: str):
        return self.db.query(Sesion).filter(
            Sesion.access_token == access_token,
            Sesion.activa == True
        ).first()

    def desactivar_sesion(self, sesion_id) -> None:
        sesion = self.db.query(Sesion).filter(Sesion.id == sesion_id).first()
        if sesion:
            sesion.activa = False
            self.db.commit()

    def actualizar_access_token(self, sesion_id, nuevo_access_token: str, nueva_fecha_expiracion: datetime) -> Sesion:
        sesion = self.db.query(Sesion).filter(Sesion.id == sesion_id).first()
        if sesion:
            sesion.access_token = nuevo_access_token
            sesion.fecha_expiracion_access = nueva_fecha_expiracion
            self.db.commit()
            self.db.refresh(sesion)
        return sesion

    def eliminar_por_usuario_id(self, usuario_id) -> None:
        self.db.query(Sesion).filter(Sesion.usuario_id == usuario_id).update({"activa": False})
        self.db.commit()
