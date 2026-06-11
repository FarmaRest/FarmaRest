# ─────────────────────────────────────────────────────────────────────────────
# CAPA: REPOSITORY – Módulo de Envíos
# Responsabilidad: Único lugar donde se ejecutan queries SQL del módulo.
# ─────────────────────────────────────────────────────────────────────────────

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.domain.envios import Envio


class EnvioRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def guardar(self, envio: Envio) -> Envio:
        self.db.add(envio)
        self.db.commit()
        self.db.refresh(envio)
        return envio

    def buscar_por_id(self, envio_id) -> Envio:
        return self.db.query(Envio).filter(Envio.id == envio_id).first()

    def buscar_por_pedido_id(self, pedido_id) -> Envio:
        return self.db.query(Envio).filter(Envio.pedido_id == pedido_id).first()

    def listar_todos(self) -> list[Envio]:
        return self.db.query(Envio).all()

    def actualizar_estado(self, envio: Envio, nuevo_estado: str) -> Envio:
        envio.estado = nuevo_estado
        envio.fecha_actualizacion = datetime.now(timezone.utc)
        self.db.flush()
        self.db.refresh(envio)
        return envio
