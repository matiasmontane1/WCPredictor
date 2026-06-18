from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import init_db
from app.models.schemas import HealthOut

# Route imports (uncommented as each router is implemented)
from app.api.routes import config as config_router
from app.api.routes import sync as sync_router
from app.api.routes import matches as matches_router
from app.api.routes import validate as validate_router
from app.api.routes import results as results_router
from app.api.routes import weights as weights_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="WCPredictor",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(config_router.router, prefix="/api/v1")
app.include_router(sync_router.router, prefix="/api/v1")
app.include_router(matches_router.router, prefix="/api/v1")
app.include_router(validate_router.router, prefix="/api/v1")
app.include_router(results_router.router, prefix="/api/v1")
app.include_router(weights_router.router, prefix="/api/v1")


@app.get("/api/v1/health", response_model=HealthOut)
async def health():
    return {"status": "ok", "version": "1.0.0"}
