from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import PredictionLog


async def create_log_entry(db: AsyncSession, data: dict) -> PredictionLog:
    log = PredictionLog(**data)
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def get_all_logs(db: AsyncSession) -> list[PredictionLog]:
    result = await db.execute(select(PredictionLog).order_by(PredictionLog.evaluated_at))
    return list(result.scalars().all())


async def get_log_count(db: AsyncSession) -> int:
    result = await db.execute(select(func.count()).select_from(PredictionLog))
    return result.scalar_one()


async def get_log_for_match(db: AsyncSession, match_id: int) -> PredictionLog | None:
    result = await db.execute(
        select(PredictionLog).where(PredictionLog.match_id == match_id)
    )
    return result.scalar_one_or_none()
