from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud import phase_config as crud
from app.models.schemas import PhaseConfigOut

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/phase/active", response_model=PhaseConfigOut)
async def get_active_phase(db: AsyncSession = Depends(get_db)):
    phase = await crud.get_active_phase(db)
    if phase is None:
        raise HTTPException(status_code=404, detail="No active phase configured")
    return phase
