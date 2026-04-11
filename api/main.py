import uvicorn
from fastapi import FastAPI, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.middleware.cors import CORSMiddleware
from .db import lifespan
from .jobs import router as jobs_router
from .admin import router as admin_router

app = FastAPI(
    title="Worker Orchestrator API",
    description="Backend para gerenciamento de jobs usando PostgreSQL como fila",
    version="1.0.0",
    lifespan=lifespan
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Adicionando Rotas
app.include_router(jobs_router)
app.include_router(admin_router)

@app.get("/metrics")
def metrics():
    """Endpoint compatível com Prometheus para exportar métricas."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/")
def root():
    return {"message": "Worker Orchestrator API is running"}

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
