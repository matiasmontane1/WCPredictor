from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import PhaseConfig
from app.models.schemas import PhaseConfigCreate


async def create_phase(db: AsyncSession, data: PhaseConfigCreate) -> PhaseConfig:
    phase = PhaseConfig(
        phase_name=data.phase_name,
        points_winner=data.points_winner,
        points_exact_score=data.points_exact_score,
        is_active=False,
    )
    db.add(phase)
    await db.commit()
    await db.refresh(phase)
    return phase


async def list_phases(db: AsyncSession) -> list[PhaseConfig]:
    result = await db.execute(select(PhaseConfig).order_by(PhaseConfig.id))
    return list(result.scalars().all())


async def get_phase(db: AsyncSession, phase_id: int) -> PhaseConfig | None:
    result = await db.execute(select(PhaseConfig).where(PhaseConfig.id == phase_id))
    return result.scalar_one_or_none()


async def get_active_phase(db: AsyncSession) -> PhaseConfig | None:
    result = await db.execute(select(PhaseConfig).where(PhaseConfig.is_active == True))
    return result.scalar_one_or_none()


async def set_active_phase(db: AsyncSession, phase_id: int) -> PhaseConfig:
    await db.execute(update(PhaseConfig).values(is_active=False))
    await db.execute(update(PhaseConfig).where(PhaseConfig.id == phase_id).values(is_active=True))
    await db.commit()
    result = await db.execute(select(PhaseConfig).where(PhaseConfig.id == phase_id))
    return result.scalar_one()


async def delete_phase(db: AsyncSession, phase_id: int) -> bool:
    phase = await get_phase(db, phase_id)
    if phase is None:
        return False
    if phase.is_active:
        raise ValueError("Cannot delete the active phase")
    await db.delete(phase)
    await db.commit()
    return True
