from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_redoc_html
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from routes import router
from app.core.cron import iniciar_cron

# Importar todos los modelos para que SQLAlchemy los registre correctamente
from app.domain.usuarios import Usuario, Direccion, HistorialCorreo, HistorialContrasena
from app.domain.autenticacion import Sesion
from app.domain.pedidos import Pedido, ItemPedido
from app.domain.productos import Producto, Lote, Presentacion, Categoria, Laboratorio
from app.domain.carritos import Carrito, ItemCarrito

app = FastAPI(
    title="FarmaRest",
    description="API REST para plataforma de ventas farmacéuticas",
    version="1.0.0",
    redoc_url=None,
)

app.include_router(router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    primer_error = exc.errors()[0] if exc.errors() else {}
    campo = ".".join(str(x) for x in primer_error.get("loc", [])[1:])
    detalle = primer_error.get("msg", "Dato inválido")
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "statusCode": 400,
            "message": "Datos de registro inválidos",
            "error": {
                "error_code": "VALIDATION_ERROR",
                "details": f"El campo '{campo}' no es válido: {detalle}" if campo else detalle,
            },
        },
    )


@app.on_event("startup")
def startup():
    iniciar_cron()

@app.get("/redoc", include_in_schema=False)
async def redoc_html() -> HTMLResponse:
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.5/bundles/redoc.standalone.js",
    )

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str

@app.get("/", tags=["Inicio"])
def root():
    return {"message": "Hola Mundo"}

@app.get(
    "/health",
    tags=["Health"],
    response_model=HealthResponse,
    summary="Estado del servicio",
    description="Verifica si la API está funcionando correctamente"
)
def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": "development"
    }