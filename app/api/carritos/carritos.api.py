from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
import importlib.util, os

_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "app", "services", "carritos", "carritos.services.py"))
_spec = importlib.util.spec_from_file_location("carritos_services", _path)
_mod  = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
CarritoService = _mod.CarritoService

router = APIRouter(prefix="/carrito", tags=["Carrito"])


# ─── Schemas de entrada ───────────────────────────────────────────────────────

class AgregarItemIn(BaseModel):
    usuario_id:  str
    producto_id: str
    cantidad:    int


class ActualizarCantidadIn(BaseModel):
    cantidad: int


# ─── Helpers de respuesta ─────────────────────────────────────────────────────

def _ok(codigo: int, mensaje: str, data=None):
    return {"success": True, "statusCode": codigo, "message": mensaje, "data": data}


def _error(codigo: int, mensaje: str, error_code: str, detalle: str):
    from datetime import datetime, timezone
    return {
        "success": False,
        "statusCode": codigo,
        "message": mensaje,
        "error": {
            "error_code": error_code,
            "details": detalle,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


def _manejar_error(e: Exception):
    msg = str(e)
    if "|" in msg:
        code, detail = msg.split("|", 1)
    else:
        code, detail = "INTERNAL_ERROR", msg

    if code == "PRODUCT_NOT_FOUND":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_error(404, "Producto no encontrado", code, detail),
        )
    if code == "INSUFFICIENT_STOCK":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_error(400, "Stock insuficiente para la cantidad solicitada", code, detail),
        )
    if code == "MAX_UNITS_EXCEEDED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_error(400, "Has superado el límite de unidades permitidas para este producto", code, detail),
        )
    if code == "MIN_PRODUCTS_NOT_MET":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_error(400, "El carrito no cumple el mínimo de productos requeridos para proceder al pago", code, detail),
        )
    if code == "CART_ITEM_NOT_FOUND":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_error(404, "Ítem no encontrado en el carrito", code, detail),
        )
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=_error(500, "Error interno del servidor", code, detail),
    )


# ─── HU-CART-01: Agregar producto al carrito ─────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
def agregar_producto(body: AgregarItemIn, db: Session = Depends(get_db)):
    try:
        service = CarritoService(db)
        data    = service.agregar_producto(body.usuario_id, body.producto_id, body.cantidad)
        return _ok(201, "Producto agregado al carrito correctamente", data)
    except (LookupError, ValueError) as e:
        _manejar_error(e)


# ─── HU-CART-01: Consultar carrito activo ────────────────────────────────────

@router.get("", status_code=status.HTTP_200_OK)
def consultar_carrito(usuario_id: str, db: Session = Depends(get_db)):
    try:
        service = CarritoService(db)
        data    = service.consultar_carrito(usuario_id)
        return _ok(200, "Carrito consultado correctamente", data)
    except Exception as e:
        _manejar_error(e)


# ─── HU-CART-01: Actualizar cantidad de ítem ─────────────────────────────────

@router.put("/{item_id}", status_code=status.HTTP_200_OK)
def actualizar_cantidad(item_id: str, body: ActualizarCantidadIn, usuario_id: str, db: Session = Depends(get_db)):
    try:
        service = CarritoService(db)
        data    = service.actualizar_cantidad(usuario_id, item_id, body.cantidad)
        return _ok(200, "Cantidad actualizada correctamente", data)
    except (LookupError, ValueError) as e:
        _manejar_error(e)


# ─── HU-CART-01: Eliminar ítem del carrito ───────────────────────────────────

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_item(item_id: str, usuario_id: str, db: Session = Depends(get_db)):
    try:
        service = CarritoService(db)
        service.eliminar_item(usuario_id, item_id)
        return None
    except LookupError as e:
        _manejar_error(e)
