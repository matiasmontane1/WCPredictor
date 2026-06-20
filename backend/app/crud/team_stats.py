from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import TeamStats


async def get_team_stats(db: AsyncSession, team_name: str) -> TeamStats | None:
    result = await db.execute(select(TeamStats).where(TeamStats.team_name == team_name))
    return result.scalar_one_or_none()


async def upsert_team_stats(db: AsyncSession, team_name: str, team_ext_id: str, data: dict) -> TeamStats:
    existing = await get_team_stats(db, team_name)
    if existing:
        existing.team_ext_id = team_ext_id
        existing.sample_size = data["sample_size"]
        existing.avg_goals_scored = data["avg_goals_scored"]
        existing.avg_goals_conceded = data["avg_goals_conceded"]
        existing.clean_sheet_pct = data["clean_sheet_pct"]
        existing.most_common_result = data["most_common_result"]
        existing.form = data["form"]
        from datetime import datetime
        existing.scraped_at = datetime.utcnow()
        await db.commit()
        await db.refresh(existing)
        return existing

    stats = TeamStats(
        team_name=team_name,
        team_ext_id=team_ext_id,
        **data,
    )
    db.add(stats)
    await db.commit()
    await db.refresh(stats)
    return stats
