from datetime import date, datetime
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import PhaseConfig

CHILE_TZ = ZoneInfo("America/Santiago")

# Fixed phase schedule — IDs are stable and referenced by Suggestion.phase_id
FIXED_PHASES = [
    {
        "id": 1,
        "phase_name": "Fase de grupos",
        "points_winner": 2,
        "points_goal_diff": 3,
        "points_exact_score": 5,
    },
    {
        "id": 2,
        "phase_name": "16avos y 8avos",
        "points_winner": 3,
        "points_goal_diff": 5,
        "points_exact_score": 8,
    },
    {
        "id": 3,
        "phase_name": "4tos en adelante",
        "points_winner": 5,
        "points_goal_diff": 7,
        "points_exact_score": 11,
    },
]


def _active_phase_id() -> int:
    today = datetime.now(CHILE_TZ).date()
    if today <= date(2026, 6, 27):
        return 1
    if today <= date(2026, 7, 7):
        return 2
    return 3


def phase_id_for_date(match_date: str) -> int:
    """Return the phase ID that was active on the given match date."""
    d = date.fromisoformat(match_date)
    if d <= date(2026, 6, 27):
        return 1
    if d <= date(2026, 7, 7):
        return 2
    return 3


async def seed_phases(db: AsyncSession) -> None:
    """Ensure the 3 fixed phases exist in the DB. Safe to call on every startup."""
    for defn in FIXED_PHASES:
        result = await db.execute(select(PhaseConfig).where(PhaseConfig.id == defn["id"]))
        if result.scalar_one_or_none() is None:
            db.add(PhaseConfig(
                id=defn["id"],
                phase_name=defn["phase_name"],
                points_winner=defn["points_winner"],
                points_goal_diff=defn["points_goal_diff"],
                points_exact_score=defn["points_exact_score"],
                is_active=False,
            ))
    await db.commit()


async def get_phase(db: AsyncSession, phase_id: int) -> PhaseConfig | None:
    result = await db.execute(select(PhaseConfig).where(PhaseConfig.id == phase_id))
    return result.scalar_one_or_none()


async def get_active_phase(db: AsyncSession) -> PhaseConfig | None:
    return await get_phase(db, _active_phase_id())
