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

# Prefijo base de las rutas de productos: /api/v1/productos
router = APIRouter(prefix="/productos", tags=["Productos"])

# Routers separados para los maestros del módulo (categorías y laboratorios).
# Se montan al mismo nivel que productos: /api/v1/categorias y /api/v1/laboratorios.
# Tienen su propio 'tags' para que aparezcan en secciones distintas en Swagger
router_categorias    = APIRouter(prefix="/categorias",    tags=["Categorías"])
router_laboratorios  = APIRouter(prefix="/laboratorios",  tags=["Laboratorios"])
router_lotes         = APIRouter(prefix="/lotes",         tags=["Lotes"])
router_presentaciones = APIRouter(prefix="/presentaciones", tags=["Presentaciones"])


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
    aplica_iva: Optional[bool] = False
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
    aplica_iva: Optional[bool] = None
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


# ─── HU-PROD-01: Consulta y filtrado del catálogo ────────────────────────────

@router.get("", status_code=status.HTTP_200_OK)
def listar_productos(
    categoria: Optional[str] = None,
    laboratorio: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Retorna el listado de productos activos. Acepta filtros opcionales por
    categoría (código) y laboratorio (nombre) vía query params.
    Siempre retorna HTTP 200, con arreglo vacío si no hay resultados.
    Endpoint público — no requiere autenticación.
    """
    try:
        service = ProductoService(db)
        productos = service.consultar_catalogo(categoria=categoria, laboratorio=laboratorio)
        data = [
            {
                "id": str(p.id),
                "nombre": p.nombre,
                "precio": float(p.precio),
                "stock": p.stock,
                "categoria": p.categoria.nombre,
                "activo": p.activo,
            }
            for p in productos
        ]
        return _formato_respuesta(200, "Productos obtenidos correctamente", data)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_formato_error(500, "Error interno del servidor", "INTERNAL_ERROR",
                                  "Ocurrió un error al consultar el catálogo de productos."),
        )


@router.get("/{producto_id}", status_code=status.HTTP_200_OK)
def consultar_producto(producto_id: str, db: Session = Depends(get_db)):
    """
    Retorna el detalle completo de un producto: categoría, laboratorio y
    presentaciones incluidas. Los productos inactivos retornan 404 para
    peticiones públicas (clientes). Endpoint público — no requiere autenticación.
    Pendiente: conectar JWT para que administradores puedan ver productos inactivos.
    """
    try:
        service = ProductoService(db)
        # Sin JWT: toda petición se trata como pública (es_admin=False)
        producto = service.consultar_por_id(producto_id, es_admin=False)
        data = {
            "id": str(producto.id),
            "nombre": producto.nombre,
            "descripcion": producto.descripcion,
            "precio": float(producto.precio),
            "aplica_iva": producto.aplica_iva,
            "stock": producto.stock,
            "activo": producto.activo,
            "categoria": {
                "nombre": producto.categoria.nombre,
                "codigo": producto.categoria.codigo,
            },
            "laboratorio": {
                "nombre": producto.laboratorio.nombre,
                "pais": producto.laboratorio.pais,
            },
            "presentaciones": [
                {"tipo": p.tipo, "cantidad": p.cantidad, "unidad": p.unidad}
                for p in producto.presentaciones
            ],
        }
        return _formato_respuesta(200, "Producto encontrado", data)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_formato_error(404, "Producto no encontrado", "PRODUCT_NOT_FOUND",
                                  "No existe un producto con el ID proporcionado"),
        )


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
            "aplica_iva": producto.aplica_iva,
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
        if "LOTE_ALREADY_EXISTS" in msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_formato_error(409, "El código de lote ya existe", "LOTE_ALREADY_EXISTS",
                                      f"Ya existe un lote con el código '{body.lote.codigoLote}'.")
            )
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


# ─── Categorías ──────────────────────────────────────────────────────────────

class CategoriaCreate(BaseModel):
    """Schema para crear una nueva categoría desde el endpoint POST /categorias."""
    nombre: str
    codigo: str


@router_categorias.get("", status_code=status.HTTP_200_OK)
def listar_categorias(db: Session = Depends(get_db)):
    """Retorna todas las categorías registradas en el sistema."""
    service = ProductoService(db)
    categorias = service.listar_categorias()
    data = [{"id": str(c.id), "nombre": c.nombre, "codigo": c.codigo} for c in categorias]
    return _formato_respuesta(200, "Categorías obtenidas correctamente", data)


@router_categorias.post("", status_code=status.HTTP_201_CREATED)
def crear_categoria(body: CategoriaCreate, db: Session = Depends(get_db)):
    """Crea una nueva categoría de productos. Solo administrador."""
    try:
        service = ProductoService(db)
        # Sin JWT por ahora — rol admin hardcodeado hasta HU de autenticación
        categoria = service.crear_categoria(body.model_dump(), solicitante_rol="admin")
        data = {
            "id":     str(categoria.id),
            "nombre": categoria.nombre,
            "codigo": categoria.codigo,
        }
        return _formato_respuesta(201, "Categoría creada correctamente", data)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_formato_error(403, "Acceso denegado", "FORBIDDEN",
                                  "Solo un administrador puede crear categorías.")
        )
    except ValueError as e:
        if "CATEGORY_ALREADY_EXISTS" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_formato_error(409, "La categoría ya existe", "CATEGORY_ALREADY_EXISTS",
                                      f"Ya existe una categoría con el código '{body.codigo}'.")
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_formato_error(400, "Datos de la categoría inválidos", "VALIDATION_ERROR", str(e))
        )


# ─── Laboratorios ────────────────────────────────────────────────────────────

class LaboratorioCreate(BaseModel):
    """Schema para crear un nuevo laboratorio desde el endpoint POST /laboratorios."""
    nombre: str
    pais: str


@router_laboratorios.get("", status_code=status.HTTP_200_OK)
def listar_laboratorios(db: Session = Depends(get_db)):
    """Retorna todos los laboratorios registrados en el sistema."""
    service = ProductoService(db)
    labs = service.listar_laboratorios()
    data = [{"id": str(l.id), "nombre": l.nombre, "pais": l.pais} for l in labs]
    return _formato_respuesta(200, "Laboratorios obtenidos correctamente", data)


@router_laboratorios.post("", status_code=status.HTTP_201_CREATED)
def crear_laboratorio(body: LaboratorioCreate, db: Session = Depends(get_db)):
    """Crea un nuevo laboratorio fabricante. Solo administrador."""
    try:
        service = ProductoService(db)
        # Sin JWT por ahora — rol admin hardcodeado hasta HU de autenticación
        laboratorio = service.crear_laboratorio(body.model_dump(), solicitante_rol="admin")
        data = {
            "id":     str(laboratorio.id),
            "nombre": laboratorio.nombre,
            "pais":   laboratorio.pais,
        }
        return _formato_respuesta(201, "Laboratorio creado correctamente", data)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_formato_error(403, "Acceso denegado", "FORBIDDEN",
                                  "Solo un administrador puede crear laboratorios.")
        )
    except ValueError as e:
        if "LAB_ALREADY_EXISTS" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_formato_error(409, "El laboratorio ya existe", "LAB_ALREADY_EXISTS",
                                      f"Ya existe un laboratorio con el nombre '{body.nombre}'.")
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_formato_error(400, "Datos del laboratorio inválidos", "VALIDATION_ERROR", str(e))
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
            "aplica_iva": producto.aplica_iva,
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


# ─── Lotes ───────────────────────────────────────────────────────────────────

class LoteAdicionalIn(BaseModel):
    """Schema para agregar un lote a un producto ya existente."""
    codigoLote: str
    fechaVencimiento: date
    cantidad: int


@router_lotes.get("/{producto_id}", status_code=status.HTTP_200_OK)
def listar_lotes(producto_id: str, db: Session = Depends(get_db)):
    """Retorna todos los lotes de un producto ordenados por fecha de vencimiento (FEFO)."""
    try:
        service = ProductoService(db)
        lotes = service.listar_lotes(producto_id)
        data = [
            {
                "id": str(l.id),
                "codigo_lote": l.codigo_lote,
                "cantidad": l.cantidad,
                "fecha_vencimiento": l.fecha_vencimiento.isoformat(),
                "fecha_ingreso": l.fecha_ingreso.isoformat(),
            }
            for l in lotes
        ]
        return _formato_respuesta(200, "Lotes obtenidos correctamente", data)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_formato_error(404, "Producto no encontrado", "PRODUCT_NOT_FOUND",
                                  "No existe un producto con el ID proporcionado")
        )


@router_lotes.post("/{producto_id}", status_code=status.HTTP_201_CREATED)
def agregar_lote(producto_id: str, body: LoteAdicionalIn, db: Session = Depends(get_db)):
    """
    Agrega un nuevo lote a un producto existente.
    Incrementa el stock del producto con la cantidad del lote y recalcula 'activo'.
    La fecha de vencimiento debe ser mayor a 15 días desde hoy.
    """
    try:
        service = ProductoService(db)
        lote, producto = service.agregar_lote(
            producto_id, body.model_dump(), solicitante_rol="admin"
        )
        data = {
            "id": str(lote.id),
            "producto_id": str(lote.producto_id),
            "codigo_lote": lote.codigo_lote,
            "cantidad": lote.cantidad,
            "fecha_vencimiento": lote.fecha_vencimiento.isoformat(),
            "stock_producto": producto.stock,
            "activo_producto": producto.activo,
        }
        return _formato_respuesta(201, "Lote agregado correctamente", data)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_formato_error(403, "Acceso denegado", "FORBIDDEN",
                                  "Solo un administrador puede agregar lotes.")
        )
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_formato_error(404, "Producto no encontrado", "PRODUCT_NOT_FOUND",
                                  "No existe un producto con el ID proporcionado")
        )
    except ValueError as e:
        msg = str(e)
        if "LOTE_ALREADY_EXISTS" in msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_formato_error(409, "El código de lote ya existe", "LOTE_ALREADY_EXISTS",
                                      f"Ya existe un lote con el código '{body.codigoLote}'.")
            )
        if "PRODUCT_NEAR_EXPIRY" in msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_formato_error(400, "Fecha de vencimiento inválida", "PRODUCT_NEAR_EXPIRY",
                                      "La fecha de vencimiento del lote debe ser mayor a 15 días desde la fecha actual.")
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_formato_error(400, "Datos del lote inválidos", "VALIDATION_ERROR", msg)
        )


# ─── Presentaciones ───────────────────────────────────────────────────────────

class PresentacionUpdate(BaseModel):
    """Schema para actualizar una presentación existente. Todos los campos son opcionales."""
    tipo: Optional[str]     = None
    cantidad: Optional[int] = None
    unidad: Optional[str]   = None


@router_presentaciones.get("/{producto_id}", status_code=status.HTTP_200_OK)
def listar_presentaciones(producto_id: str, db: Session = Depends(get_db)):
    """Retorna todas las presentaciones comerciales de un producto."""
    try:
        service = ProductoService(db)
        presentaciones = service.listar_presentaciones(producto_id)
        data = [
            {
                "id": str(p.id),
                "tipo": p.tipo,
                "cantidad": p.cantidad,
                "unidad": p.unidad,
            }
            for p in presentaciones
        ]
        return _formato_respuesta(200, "Presentaciones obtenidas correctamente", data)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_formato_error(404, "Producto no encontrado", "PRODUCT_NOT_FOUND",
                                  "No existe un producto con el ID proporcionado")
        )


@router_presentaciones.put("/{presentacion_id}", status_code=status.HTTP_200_OK)
def actualizar_presentacion(presentacion_id: str, body: PresentacionUpdate, db: Session = Depends(get_db)):
    """Actualiza los datos de una presentación existente (tipo, cantidad o unidad)."""
    try:
        service = ProductoService(db)
        presentacion = service.actualizar_presentacion(
            presentacion_id, body.model_dump(exclude_none=True), solicitante_rol="admin"
        )
        data = {
            "id": str(presentacion.id),
            "producto_id": str(presentacion.producto_id),
            "tipo": presentacion.tipo,
            "cantidad": presentacion.cantidad,
            "unidad": presentacion.unidad,
        }
        return _formato_respuesta(200, "Presentación actualizada correctamente", data)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_formato_error(403, "Acceso denegado", "FORBIDDEN",
                                  "Solo un administrador puede modificar presentaciones.")
        )
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_formato_error(404, "Presentación no encontrada", "PRESENTACION_NOT_FOUND",
                                  "No existe una presentación con el ID proporcionado")
        )
