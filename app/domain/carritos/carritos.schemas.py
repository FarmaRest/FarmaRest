from pydantic import BaseModel, UUID4
from datetime import datetime
from decimal import Decimal
from typing import List


class ItemCarritoIn(BaseModel):
    producto_id: UUID4
    cantidad: int


class ItemCarritoOut(BaseModel):
    id: UUID4
    carrito_id: UUID4
    producto_id: UUID4
    nombre: str | None = None
    cantidad: int
    precio_unitario: Decimal
    iva_unitario: Decimal
    subtotal: Decimal

    model_config = {"from_attributes": True}


class CarritoIn(BaseModel):
    usuario_id: UUID4


class CarritoOut(BaseModel):
    id: UUID4
    usuario_id: UUID4
    subtotal_base: Decimal
    total_iva: Decimal
    total: Decimal
    activo: bool
    fecha_creacion: datetime
    items: List[ItemCarritoOut] = []

    model_config = {"from_attributes": True}
