# ─────────────────────────────────────────────────────────────────────────────
# CAPA: REPOSITORY – Módulo de Pagos
# Responsabilidad: Único lugar donde se ejecutan queries SQL del módulo.
# ─────────────────────────────────────────────────────────────────────────────

from sqlalchemy.orm import Session
from datetime import datetime, timezone
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

    def actualizar_desde_webhook(self, pago: Pago, estado_transaccion: str, id_transaccion_wompi: str, metodo_pago: str) -> Pago:
        pago.estado_transaccion = estado_transaccion
        pago.id_transaccion_wompi = id_transaccion_wompi
        pago.metodo_pago = metodo_pago
        pago.fecha_actualizacion = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(pago)
        return pago

    def actualizar_estado_manual(self, pago: Pago, estado_transaccion: str) -> Pago:
        pago.estado_transaccion = estado_transaccion
        pago.fecha_actualizacion = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(pago)
        return pago
