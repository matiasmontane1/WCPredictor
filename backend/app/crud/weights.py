from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import ModelWeights


async def get_weights(db: AsyncSession) -> ModelWeights:
    result = await db.execute(select(ModelWeights).where(ModelWeights.id == 1))
    weights = result.scalar_one_or_none()
    if weights is None:
        weights = ModelWeights(id=1, weight_xg=0.5, weight_market=0.5, matches_evaluated=0)
        db.add(weights)
        await db.commit()
        await db.refresh(weights)
    return weights


async def update_weights(db: AsyncSession, weight_xg: float, weight_market: float, matches_evaluated: int) -> ModelWeights:
    weights = await get_weights(db)
    weights.weight_xg = weight_xg
    weights.weight_market = weight_market
    weights.matches_evaluated = matches_evaluated
    weights.last_updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(weights)
    return weights
