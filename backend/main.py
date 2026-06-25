import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import AsyncSessionLocal, init_db
from app.core.config import settings
from app.models.schemas import HealthOut
from app.services.sync_service import run_daily_sync
from app.crud.phase_config import seed_phases

# Route imports (uncommented as each router is implemented)
from app.services.smart_scheduler import schedule_today_syncs, CHILE_TZ
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

    scheduler = AsyncIOScheduler()
    scheduler.start()

    # Startup sync (awaited so DB is populated before scheduling today's jobs).
    await _auto_sync()

    # Schedule optimal sync times for today based on actual match kickoffs.
    await schedule_today_syncs(scheduler)

    # Daily planner: re-computes and re-registers the day's sync jobs at 00:30 CLT.
    scheduler.add_job(
        schedule_today_syncs,
        CronTrigger(hour=0, minute=30, timezone=CHILE_TZ),
        args=[scheduler],
        id="daily_planner",
        replace_existing=True,
    )

    app.state.scheduler = scheduler

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
