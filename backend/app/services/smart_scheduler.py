import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from app.core.database import AsyncSessionLocal
from app.crud.matches import get_matches_for_date
from app.services.sync_service import run_daily_sync

_EARLY_MORNING_CUTOFF_HOUR = 6  # include yesterday's matches before this hour

logger = logging.getLogger(__name__)

CHILE_TZ = ZoneInfo("America/Santiago")
_PRE_OFFSET = timedelta(hours=1)
_POST_OFFSET = timedelta(hours=2, minutes=15)
_MERGE_GAP = timedelta(hours=1)


def _merge_sync_times(times: list[datetime]) -> list[datetime]:
    """Iteratively merge adjacent times < 1 hour apart into the later of the two."""
    if not times:
        return []
    times = sorted(times)
    changed = True
    while changed:
        changed = False
        result = []
        i = 0
        while i < len(times):
            if i + 1 < len(times) and times[i + 1] - times[i] < _MERGE_GAP:
                result.append(times[i + 1])
                i += 2
                changed = True
            else:
                result.append(times[i])
                i += 1
        times = result
    return times


def _compute_sync_times(matches, now_utc: datetime) -> list[datetime]:
    """
    Given matches for today, compute pre-match (kickoff - 1h) and post-match
    (kickoff + 2h15m) sync times, discard past times, then merge those < 1h apart.

    Kickoff times may be stored in any timezone (from football-data.org); all
    arithmetic is done in UTC so the Chile server clock doesn't affect correctness.
    """
    raw: list[datetime] = []
    for match in matches:
        if not match.kickoff_time:
            continue
        try:
            kickoff = datetime.fromisoformat(match.kickoff_time.replace("Z", "+00:00"))
            if kickoff.tzinfo is None:
                kickoff = kickoff.replace(tzinfo=timezone.utc)
            kickoff = kickoff.astimezone(timezone.utc)
        except Exception:
            logger.warning("[SmartScheduler] Bad kickoff_time match %s: %s", match.id, match.kickoff_time)
            continue

        pre = kickoff - _PRE_OFFSET
        post = kickoff + _POST_OFFSET

        if pre > now_utc + timedelta(minutes=1):
            raw.append(pre)
        if post > now_utc + timedelta(minutes=1):
            raw.append(post)

    return _merge_sync_times(raw)


async def _run_sync() -> None:
    async with AsyncSessionLocal() as db:
        job_id = f"smart_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        await run_daily_sync(db, job_id)


async def schedule_today_syncs(scheduler: AsyncIOScheduler) -> None:
    """
    Read today's full match schedule from the DB, compute optimal sync times
    (pre-match and post-match, merged when < 1h apart), and register one-shot
    APScheduler jobs.

    Called at 00:30 CLT each day via a daily cron, and once on startup after
    the initial sync populates the DB.
    """
    # Remove any previously scheduled smart-sync jobs to avoid duplicates.
    for job in scheduler.get_jobs():
        if job.id.startswith("smart_sync_"):
            job.remove()

    now_chile = datetime.now(CHILE_TZ)
    today_str = now_chile.date().isoformat()
    async with AsyncSessionLocal() as db:
        matches = list(await get_matches_for_date(db, today_str))
        # Before 6 AM, a late match from yesterday may still have a future
        # post-match sync (e.g. kickoff 22:45 → sync 01:00). Include it so
        # the job isn't silently dropped when the planner removes all smart_sync_*.
        if now_chile.hour < _EARLY_MORNING_CUTOFF_HOUR:
            yesterday_str = (now_chile.date() - timedelta(days=1)).isoformat()
            matches += list(await get_matches_for_date(db, yesterday_str))

    now_utc = datetime.now(timezone.utc)
    sync_times = _compute_sync_times(matches, now_utc)

    if not sync_times:
        logger.info("[SmartScheduler] No upcoming syncs to schedule for %s.", today_str)
        return

    for t in sync_times:
        job_id = f"smart_sync_{t.strftime('%H%M%S')}"
        scheduler.add_job(
            _run_sync,
            DateTrigger(run_date=t),
            id=job_id,
            replace_existing=True,
        )
        t_chile = t.astimezone(CHILE_TZ)
        logger.info(
            "[SmartScheduler] Sync at %s CLT  (%s UTC)",
            t_chile.strftime("%H:%M"),
            t.strftime("%H:%M"),
        )

    logger.info("[SmartScheduler] %d sync(s) scheduled for %s.", len(sync_times), today_str)
