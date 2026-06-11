# ─────────────────────────────────────────────────────────────────────────────
# CAPA: REPOSITORY – Módulo de Pagos
# Responsabilidad: Único lugar donde se ejecutan queries SQL del módulo.
# ─────────────────────────────────────────────────────────────────────────────

from sqlalchemy.orm import Session
from app.domain.pagos import Pago


class PagoRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def guardar(self, pago: Pago) -> Pago:
        self.db.add(pago)
        self.db.flush()
        return pago

    def buscar_por_id(self, pago_id) -> Pago:
        return self.db.query(Pago).filter(Pago.id == pago_id).first()

    def buscar_por_referencia(self, referencia_interna: str) -> Pago:
        return self.db.query(Pago).filter(Pago.referencia_interna == referencia_interna).first()

    def listar_todos(self) -> list:
        return self.db.query(Pago).order_by(Pago.fecha_creacion.desc()).all()
