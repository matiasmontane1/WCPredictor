from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import ScrapedMetrics


async def upsert_metrics(db: AsyncSession, match_id: int, metrics_data: dict) -> ScrapedMetrics:
    result = await db.execute(
        select(ScrapedMetrics).where(ScrapedMetrics.match_id == match_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        for key, value in metrics_data.items():
            if value is not None:
                setattr(existing, key, value)
        await db.commit()
        await db.refresh(existing)
        return existing
    metrics = ScrapedMetrics(match_id=match_id, **metrics_data)
    db.add(metrics)
    await db.commit()
    await db.refresh(metrics)
    return metrics


async def get_metrics_for_match(db: AsyncSession, match_id: int) -> ScrapedMetrics | None:
    result = await db.execute(
        select(ScrapedMetrics).where(ScrapedMetrics.match_id == match_id)
    )
    return result.scalar_one_or_none()
