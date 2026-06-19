from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import select

CHILE_TZ = ZoneInfo("America/Santiago")
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import Match


async def upsert_match(db: AsyncSession, match_data: dict) -> Match:
    result = await db.execute(
        select(Match).where(Match.external_id == match_data["external_id"])
    )
    existing = result.scalar_one_or_none()
    if existing:
        for key, value in match_data.items():
            if key not in ("actual_home_goals", "actual_away_goals"):
                setattr(existing, key, value)
        await db.commit()
        await db.refresh(existing)
        return existing
    match = Match(**match_data)
    db.add(match)
    await db.commit()
    await db.refresh(match)
    return match


async def get_today_matches(db: AsyncSession) -> list[Match]:
    today = datetime.now(CHILE_TZ).date().isoformat()
    result = await db.execute(
        select(Match).where(Match.match_date == today).order_by(Match.kickoff_time)
    )
    return list(result.scalars().all())


async def get_yesterday_matches(db: AsyncSession) -> list[Match]:
    yesterday = (datetime.now(CHILE_TZ).date() - timedelta(days=1)).isoformat()
    result = await db.execute(
        select(Match).where(Match.match_date == yesterday).order_by(Match.kickoff_time)
    )
    return list(result.scalars().all())


async def get_all_matches(db: AsyncSession) -> list[Match]:
    result = await db.execute(select(Match).order_by(Match.match_date, Match.kickoff_time))
    return list(result.scalars().all())


async def get_match_by_id(db: AsyncSession, match_id: int) -> Match | None:
    result = await db.execute(select(Match).where(Match.id == match_id))
    return result.scalar_one_or_none()


async def set_match_result(db: AsyncSession, match_id: int, home_goals: int, away_goals: int) -> Match:
    match = await get_match_by_id(db, match_id)
    if match is None:
        raise ValueError("Match not found")
    match.actual_home_goals = home_goals
    match.actual_away_goals = away_goals
    match.status = "finished"
    await db.commit()
    await db.refresh(match)
    return match
