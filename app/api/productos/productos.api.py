# ─────────────────────────────────────────────────────────────────────────────
# CAPA: API — Módulo de Productos
# Responsabilidad: Expone los endpoints HTTP del catálogo. Valida que el JSON
# recibido tenga el formato correcto usando schemas Pydantic v2, delega al
# servicio correspondiente y retorna la respuesta estructurada.
# No contiene reglas de negocio ni accede directamente a la BD.
# ─────────────────────────────────────────────────────────────────────────────

from datetime import date, datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.productos import ProductoService

# Prefijo base de todas las rutas de este módulo: /api/v1/productos
router = APIRouter(prefix="/productos", tags=["Productos"])


# ─── Schemas de entrada ──────────────────────────────────────────────────────
# Los nombres de los campos usan camelCase tal y como lo exige el contrato
# de la HU-PROD-02 (codigoLote, fechaVencimiento). Pydantic v2 valida los
# tipos automáticamente y retorna 422 si algún campo viene mal formado.

class LoteIn(BaseModel):
    """Lote inicial del producto. Llega anidado dentro del body de POST."""
    codigoLote: str
    fechaVencimiento: date    # Pydantic acepta strings ISO ("2026-12-31")
    cantidad: int


class CategoriaIn(BaseModel):
    """Referencia a la categoría. Se busca por 'codigo' en la BD (debe existir)."""
    nombre: str
    codigo: str


class LaboratorioIn(BaseModel):
    """Referencia al laboratorio. Se busca por 'nombre' en la BD (debe existir)."""
    nombre: str
    pais: str


class PresentacionIn(BaseModel):
    """Presentación comercial del producto (caja x20, frasco 60ml, etc.)."""
    tipo: str
    cantidad: int
    unidad: str


class ProductoIn(BaseModel):
    """Schema completo para registrar un nuevo producto (POST /productos)."""
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    stock: int
    # El cliente puede mandar 'activo' pero el sistema lo recalcula:
    # stock = 0 → false; stock > 0 con vencimiento OK → true
    activo: Optional[bool] = None
    lote: LoteIn
    categoria: CategoriaIn
    laboratorio: LaboratorioIn
    presentaciones: Optional[list[PresentacionIn]] = Field(default_factory=list)


class ProductoUpdate(BaseModel):
    """
    Schema para actualizar producto (PUT /productos/{id}).
    Todos los campos son opcionales — solo se actualiza lo enviado.
    NO permite cambiar lote, categoría, laboratorio ni presentaciones
    (eso pertenece a HUs de inventario más adelante).
    """
    nombre: Optional[str]      = None
    descripcion: Optional[str] = None
    precio: Optional[float]    = None
    stock: Optional[int]       = None
    activo: Optional[bool]     = None


# ─── Helpers de respuesta ────────────────────────────────────────────────────
# Mantienen el formato estándar usado en todo el proyecto (igual que usuarios)

def _formato_respuesta(codigo: int, mensaje: str, data=None):
    """Estructura estándar para respuestas exitosas."""
    return {"success": True, "statusCode": codigo, "message": mensaje, "data": data}


def _formato_error(codigo: int, mensaje: str, error_code: str, detalle: str):
    """Estructura estándar para respuestas de error con timestamp UTC."""
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


# ─── HU-PROD-02: Registro de producto ────────────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
def registrar_producto(body: ProductoIn, db: Session = Depends(get_db)):
    """
    Registra un nuevo producto en el catálogo junto con su lote inicial
    y sus presentaciones. Aplica las siguientes reglas:
    - precio > 0
    - fechaVencimiento del lote > 15 días desde hoy
    - categoría y laboratorio deben existir previamente
    - 'activo' se calcula automáticamente según stock y vencimiento

    Pendiente: conectar JWT cuando la HU de autenticación esté lista.
    """
    try:
        service = ProductoService(db)
        # Sin JWT por ahora — rol admin hardcodeado hasta HU de autenticación
        producto, lote, categoria, laboratorio = service.registrar_producto(
            body.model_dump(), solicitante_rol="admin"
        )

        data = {
            "id": str(producto.id),
            "nombre": producto.nombre,
            "precio": float(producto.precio),
            "stock": producto.stock,
            "lote": lote.codigo_lote,
            "fecha_vencimiento": lote.fecha_vencimiento.isoformat(),
            "categoria": categoria.nombre,
            "laboratorio": laboratorio.nombre,
            "activo": producto.activo,
        }
        return _formato_respuesta(201, "Producto registrado correctamente", data)

    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_formato_error(403, "Acceso denegado", "FORBIDDEN",
                                  "Solo un administrador puede registrar o modificar productos.")
        )
    except LookupError as e:
        msg = str(e)
        if "CATEGORY_NOT_FOUND" in msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=_formato_error(404, "Categoría no encontrada", "CATEGORY_NOT_FOUND",
                                      f"No existe una categoría con el código '{body.categoria.codigo}'.")
            )
        if "LAB_NOT_FOUND" in msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=_formato_error(404, "Laboratorio no encontrado", "LAB_NOT_FOUND",
                                      f"No existe un laboratorio con el nombre '{body.laboratorio.nombre}'.")
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_formato_error(404, "Recurso no encontrado", "NOT_FOUND", msg)
        )
    except ValueError as e:
        msg = str(e)
        if "INVALID_PRICE" in msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_formato_error(400, "El precio del producto no es válido", "INVALID_PRICE",
                                      "El precio del producto debe ser mayor a cero.")
            )
        if "PRODUCT_NEAR_EXPIRY" in msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_formato_error(400, "El producto no puede registrarse en el catálogo",
                                      "PRODUCT_NEAR_EXPIRY",
                                      "La fecha de vencimiento del lote debe ser mayor a 15 días desde la fecha actual para poder publicar el producto.")
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_formato_error(400, "Datos del producto inválidos", "VALIDATION_ERROR", msg)
        )


# ─── HU-PROD-02: Actualización de producto ───────────────────────────────────

@router.put("/{producto_id}", status_code=status.HTTP_200_OK)
def actualizar_producto(producto_id: str, body: ProductoUpdate, db: Session = Depends(get_db)):
    """
    Actualiza los campos modificables de un producto existente.
    Solo se modifican los campos enviados en el body. Si se actualiza
    'stock', el sistema recalcula 'activo' automáticamente consultando
    el lote vigente del producto.

    Pendiente: conectar JWT cuando la HU de autenticación esté lista.
    """
    try:
        service = ProductoService(db)
        # Sin JWT por ahora — rol admin hardcodeado hasta HU de autenticación
        producto = service.actualizar_producto(
            producto_id, body.model_dump(exclude_none=True), solicitante_rol="admin"
        )

        data = {
            "id": str(producto.id),
            "nombre": producto.nombre,
            "descripcion": producto.descripcion,
            "precio": float(producto.precio),
            "stock": producto.stock,
            "activo": producto.activo,
        }
        return _formato_respuesta(200, "Producto actualizado correctamente", data)

    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_formato_error(403, "Acceso denegado", "FORBIDDEN",
                                  "Solo un administrador puede registrar o modificar productos.")
        )
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_formato_error(404, "Producto no encontrado", "PRODUCT_NOT_FOUND",
                                  "No existe un producto con el ID proporcionado")
        )
    except ValueError as e:
        msg = str(e)
        if "INVALID_PRICE" in msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_formato_error(400, "El precio del producto no es válido", "INVALID_PRICE",
                                      "El precio del producto debe ser mayor a cero.")
            )
        if "INVALID_STOCK" in msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_formato_error(400, "El stock del producto no es válido", "INVALID_STOCK",
                                      "El stock del producto no puede ser negativo.")
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_formato_error(400, "Datos del producto inválidos", "VALIDATION_ERROR", msg)
        )
