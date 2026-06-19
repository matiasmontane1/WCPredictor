from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud.weights import get_weights, update_weights
from app.crud.prediction_log import delete_all_logs, get_log_count
from app.models.schemas import ModelWeightsOut

router = APIRouter(prefix="/weights", tags=["weights"])


@router.get("", response_model=ModelWeightsOut)
async def get_model_weights(db: AsyncSession = Depends(get_db)):
    return await get_weights(db)


@router.post("/reset", response_model=ModelWeightsOut)
async def reset_weights(db: AsyncSession = Depends(get_db)):
    """Delete all prediction logs and reset weights to 50/50."""
    await delete_all_logs(db)
    return await update_weights(db, 0.5, 0.5, 0)
