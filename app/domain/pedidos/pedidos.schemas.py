# ─────────────────────────────────────────────────────────────────────────────
# CAPA: DOMAIN – Módulo de Pedidos
# Responsabilidad: Schemas Pydantic v2 para validación y serialización.
# ─────────────────────────────────────────────────────────────────────────────

from pydantic import BaseModel, UUID4, Field
from datetime import datetime
from decimal import Decimal


class ItemPedidoSalida(BaseModel):
    id:              UUID4
    pedido_id:       UUID4
    producto_id:     UUID4
    cantidad:        int
    precio_unitario: Decimal
    iva_unitario:    Decimal
    subtotal:        Decimal

    model_config = {"from_attributes": True}


class DireccionEntradaSchema(BaseModel):
    direccion: str = Field(..., max_length=200)
    ciudad:    str = Field(..., max_length=100)


class PedidoEntrada(BaseModel):
    carrito_id:        UUID4
    direccion_entrega: DireccionEntradaSchema
    metodo_pago:       str = Field(..., max_length=50)


class PedidoSalida(BaseModel):
    id:                  UUID4
    usuario_id:          UUID4
    carrito_id:          UUID4
    estado:              str
    subtotal_base:       Decimal
    total_iva:           Decimal
    total:               Decimal
    direccion_entrega:   str
    ciudad_entrega:      str
    metodo_pago:         str
    fecha_creacion:      datetime
    fecha_actualizacion: datetime
    items:               list[ItemPedidoSalida] = []

    model_config = {"from_attributes": True}