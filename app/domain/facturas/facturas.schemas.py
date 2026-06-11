# ─────────────────────────────────────────────────────────────────────────────
# CAPA: DOMAIN – Módulo de Facturas
# Responsabilidad: Define los schemas Pydantic v2 para validación de entrada
# y serialización de salida del módulo de facturas electrónicas.
# ─────────────────────────────────────────────────────────────────────────────

from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional


class FacturaEntrada(BaseModel):
    pagoId: UUID4


class FacturaSalida(BaseModel):
    id:             UUID4
    numero_factura: str
    pago_id:        UUID4
    pedido_id:      UUID4
    usuario_id:     UUID4
    subtotal_base:  float
    total_iva:      float
    total:          float
    cufe:           Optional[str] = None
    factus_id:      Optional[str] = None
    url_pdf:        Optional[str] = None
    url_xml:        Optional[str] = None
    estado_dian:    str
    fecha_emision:  datetime

    model_config = {"from_attributes": True}
