from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud.weights import get_weights, update_weights
from app.crud.prediction_log import delete_all_logs, get_all_logs
from app.models.schemas import FeedbackLogItem, FeedbackLogsOut, ModelWeightsOut

router = APIRouter(prefix="/weights", tags=["weights"])


@router.get("", response_model=ModelWeightsOut)
async def get_model_weights(db: AsyncSession = Depends(get_db)):
    return await get_weights(db)


@router.get("/logs", response_model=FeedbackLogsOut)
async def get_feedback_logs(db: AsyncSession = Depends(get_db)):
    logs = await get_all_logs(db)
    items = [
        FeedbackLogItem(
            match_id=l.match_id,
            actual_score=f"{l.actual_home_goals}-{l.actual_away_goals}",
            brier_xg=l.model_a_error,
            brier_market=l.model_b_error,
            weight_xg_before=l.weight_xg_before,
            weight_market_before=l.weight_market_before,
            weight_xg_after=l.weight_xg_after,
            weight_market_after=l.weight_market_after,
            evaluated_at=l.evaluated_at.isoformat() if l.evaluated_at else None,
        )
        for l in logs
    ]
    return FeedbackLogsOut(total_logs=len(items), logs=items)


@router.post("/reset", response_model=ModelWeightsOut)
async def reset_weights(db: AsyncSession = Depends(get_db)):
    """Delete all prediction logs and reset weights to 50/50."""
    await delete_all_logs(db)
    return await update_weights(db, 0.5, 0.5, 0)
