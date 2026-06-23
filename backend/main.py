import asyncio
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import AsyncSessionLocal, init_db
from app.core.config import settings
from app.models.schemas import HealthOut
from app.services.sync_service import run_daily_sync
from app.crud.phase_config import seed_phases

# Route imports (uncommented as each router is implemented)
from app.api.routes import config as config_router
from app.api.routes import sync as sync_router
from app.api.routes import matches as matches_router
from app.api.routes import validate as validate_router
from app.api.routes import results as results_router
from app.api.routes import weights as weights_router
from app.api.routes import stats as stats_router

logger = logging.getLogger(__name__)


async def _auto_sync():
    async with AsyncSessionLocal() as db:
        await run_daily_sync(db, "auto")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.is_production:
        await init_db()

    async with AsyncSessionLocal() as db:
        await seed_phases(db)

    # Startup sync
    asyncio.create_task(_auto_sync())

    # Auto-sync every 4 hours
    scheduler = AsyncIOScheduler()
    scheduler.add_job(_auto_sync, IntervalTrigger(hours=4))
    scheduler.start()

    yield

    scheduler.shutdown(wait=False)


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
app.include_router(stats_router.router, prefix="/api/v1")


@app.get("/api/v1/health", response_model=HealthOut)
async def health():
    return {"status": "ok", "version": "1.0.0"}
