from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud import phase_config as crud
from app.models.schemas import PhaseConfigCreate, PhaseConfigOut

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/phase", response_model=list[PhaseConfigOut])
async def list_phases(db: AsyncSession = Depends(get_db)):
    return await crud.list_phases(db)


@router.post("/phase", response_model=PhaseConfigOut, status_code=201)
async def create_phase(data: PhaseConfigCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_phase(db, data)


@router.put("/phase/{phase_id}/activate", response_model=PhaseConfigOut)
async def activate_phase(phase_id: int, db: AsyncSession = Depends(get_db)):
    phase = await crud.get_phase(db, phase_id)
    if phase is None:
        raise HTTPException(status_code=404, detail="Phase config not found")
    return await crud.set_active_phase(db, phase_id)


@router.delete("/phase/{phase_id}", status_code=204)
async def delete_phase(phase_id: int, db: AsyncSession = Depends(get_db)):
    phase = await crud.get_phase(db, phase_id)
    if phase is None:
        raise HTTPException(status_code=404, detail="Phase config not found")
    try:
        await crud.delete_phase(db, phase_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
