from pydantic import BaseModel, UUID4
from datetime import datetime


class SesionIn(BaseModel):
    usuario_id: UUID4
    access_token: str
    refresh_token: str
    fecha_expiracion_access: datetime
    fecha_expiracion_refresh: datetime


class SesionOut(BaseModel):
    id: UUID4
    usuario_id: UUID4
    access_token: str
    refresh_token: str
    fecha_expiracion_access: datetime
    fecha_expiracion_refresh: datetime
    fecha_creacion: datetime
    activa: bool

    model_config = {"from_attributes": True}