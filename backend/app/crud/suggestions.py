from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import Suggestion


_ORM_FIELDS = {"score_home", "score_away", "probability", "ev", "suggestion_type"}

async def upsert_suggestions(db: AsyncSession, match_id: int, suggestions: list[dict]) -> None:
    await db.execute(delete(Suggestion).where(Suggestion.match_id == match_id))
    for s in suggestions:
        orm_data = {k: v for k, v in s.items() if k in _ORM_FIELDS}
        db.add(Suggestion(match_id=match_id, **orm_data))
    await db.commit()


async def get_suggestions_for_match(db: AsyncSession, match_id: int) -> list[Suggestion]:
    result = await db.execute(
        select(Suggestion).where(Suggestion.match_id == match_id)
    )
    return list(result.scalars().all())
