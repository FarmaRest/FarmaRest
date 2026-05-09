from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hola Mundo"}

@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": "development"
    }