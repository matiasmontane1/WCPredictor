from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud.weights import get_weights
from app.models.schemas import ModelWeightsOut

router = APIRouter(prefix="/weights", tags=["weights"])


@router.get("", response_model=ModelWeightsOut)
async def get_model_weights(db: AsyncSession = Depends(get_db)):
    return await get_weights(db)
