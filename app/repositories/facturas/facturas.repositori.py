# ─────────────────────────────────────────────────────────────────────────────
# CAPA: REPOSITORY – Módulo de Facturas
# Responsabilidad: Único lugar donde se ejecutan queries SQL del módulo.
# ─────────────────────────────────────────────────────────────────────────────

from sqlalchemy.orm import Session
from app.domain.pagos import Factura


class FacturaRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def guardar(self, factura: Factura) -> Factura:
        self.db.add(factura)
        self.db.commit()
        self.db.refresh(factura)
        return factura

    def buscar_por_id(self, factura_id) -> Factura:
        return self.db.query(Factura).filter(Factura.id == factura_id).first()

    def buscar_por_pago_id(self, pago_id) -> Factura:
        return self.db.query(Factura).filter(Factura.pago_id == pago_id).first()

    def obtener_ultimo_numero(self) -> str:
        ultima = self.db.query(Factura).order_by(Factura.numero_factura.desc()).first()
        return ultima.numero_factura if ultima else None

    def actualizar_emision(self, factura: Factura, cufe: str, factus_id: str, url_pdf: str, url_xml: str, estado_dian: str) -> Factura:
        factura.cufe = cufe
        factura.factus_id = factus_id
        factura.url_pdf = url_pdf
        factura.url_xml = url_xml
        factura.estado_dian = estado_dian
        self.db.commit()
        self.db.refresh(factura)
        return factura

    def actualizar_estado_dian(self, factura: Factura, estado_dian: str) -> Factura:
        factura.estado_dian = estado_dian
        self.db.commit()
        self.db.refresh(factura)
        return factura
