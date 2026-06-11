# ─────────────────────────────────────────────────────────────────────────────
# CAPA: DOMAIN – Módulo de Pagos
# Responsabilidad: Define los schemas Pydantic v2 para validación de entrada
# y serialización de salida del módulo de pagos.
# ─────────────────────────────────────────────────────────────────────────────

from pydantic import BaseModel, UUID4, Field
from datetime import datetime
from typing import Optional


class PagoEntrada(BaseModel):
    pedidoId:        UUID4
    montoEnCentavos: int = Field(..., gt=0)
    moneda:          str = Field(default="COP", max_length=10)
    correoCliente:   str = Field(..., max_length=200)


class WompiSignature(BaseModel):
    checksum:   str
    properties: list[str]


class WompiTransactionData(BaseModel):
    id:                  str
    reference:           str
    status:              str
    amount_in_cents:     int
    currency:            str
    payment_method_type: Optional[str] = None


class WebhookWompiEntrada(BaseModel):
    event:     str
    data:      WompiTransactionData
    signature: WompiSignature


class PagoSalida(BaseModel):
    id:                   UUID4
    pedido_id:            UUID4
    usuario_id:           UUID4
    referencia_interna:   str
    id_transaccion_wompi: Optional[str] = None
    monto_en_centavos:    int
    moneda:               str
    metodo_pago:          Optional[str] = None
    estado_transaccion:   str
    url_checkout:         Optional[str] = None
    fecha_creacion:       datetime
    fecha_actualizacion:  datetime

    model_config = {"from_attributes": True}
