from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas import SyncResponse, SyncStatusResponse
from app.services.sync_service import job_status, run_daily_sync

router = APIRouter(prefix="/sync", tags=["sync"])

CHILE_TZ = ZoneInfo("America/Santiago")


@router.post("", response_model=SyncResponse, status_code=202)
async def trigger_sync(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    job_id = f"sync_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    job_status[job_id] = {
        "job_id": job_id,
        "status": "started",
        "started_at": datetime.utcnow().isoformat(),
    }
    background_tasks.add_task(run_daily_sync, db, job_id)
    return SyncResponse(
        job_id=job_id,
        status="started",
        message=f"Sync running in background. Check /api/v1/sync/status/{job_id} for progress.",
    )


@router.get("/schedule")
async def sync_schedule(request: Request):
    """Return upcoming smart-sync job times scheduled for today."""
    scheduler = getattr(request.app.state, "scheduler", None)
    if scheduler is None:
        return {"scheduled": [], "next": None}

    times: list[str] = []
    for job in scheduler.get_jobs():
        if job.next_run_time is None:
            continue
        if job.id.startswith("smart_sync_") or job.id == "daily_planner":
            times.append(job.next_run_time.isoformat())

    times.sort()
    return {"scheduled": times, "next": times[0] if times else None}


@router.get("/status/{job_id}", response_model=SyncStatusResponse)
async def sync_status(job_id: str):
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    data = job_status[job_id]
    return SyncStatusResponse(
        job_id=data["job_id"],
        status=data["status"],
        started_at=data.get("started_at"),
        completed_at=data.get("completed_at"),
        results=data.get("results"),
    )
