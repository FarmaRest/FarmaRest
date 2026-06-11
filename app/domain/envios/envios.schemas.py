# ─────────────────────────────────────────────────────────────────────────────
# CAPA: DOMAIN – Módulo de Envíos
# Responsabilidad: Define los schemas Pydantic v2 para validación de entrada
# y serialización de salida del módulo de envíos.
# ─────────────────────────────────────────────────────────────────────────────

from pydantic import BaseModel, UUID4, Field
from datetime import date, datetime


class DireccionEntrega(BaseModel):
    direccion: str = Field(..., max_length=200)
    ciudad:    str = Field(..., max_length=100)


class EnvioEntrada(BaseModel):
    pedidoId:          UUID4
    usuarioId:         UUID4
    direccionEntrega:  DireccionEntrega
    empresaTransporte: str = Field(..., max_length=100)
    fechaDespacho:     date


class EnvioSalida(BaseModel):
    id:                  UUID4
    pedido_id:           UUID4
    usuario_id:          UUID4
    estado:              str
    direccion_entrega:   str
    ciudad_entrega:      str
    empresa_transporte:  str
    fecha_despacho:      date
    costo_envio:         float
    fecha_creacion:      datetime
    fecha_actualizacion: datetime

    model_config = {"from_attributes": True}
