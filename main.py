from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(
    title="Mi API",
    description="API de prueba con FastAPI",
    version="1.0.0",
    redoc_url=None,  # deshabilitar el redoc automático
)

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
    """
    Endpoint principal
    """
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