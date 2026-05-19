from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from routes import router
from app.core.cron import iniciar_cron

app = FastAPI(
    title="FarmaRest",
    description="API REST para plataforma de ventas farmacéuticas",
    version="1.0.0",
    redoc_url=None,
)

app.include_router(router)


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