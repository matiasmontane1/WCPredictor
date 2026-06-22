import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud import metrics as metrics_crud
from app.crud.weights import get_weights, update_weights
from app.crud.prediction_log import delete_all_logs, get_all_logs
from app.models.orm import ScrapedMetrics
from app.models.schemas import FeedbackLogItem, FeedbackLogsOut, ModelWeightsOut
from app.services.scrapers.elo_scraper import get_elo_lambdas

_executor = ThreadPoolExecutor(max_workers=2)

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


@router.post("/backfill-elo")
async def backfill_elo(db: AsyncSession = Depends(get_db)):
    """Retroactively set Elo-based lambda_xg for all matches that have market metrics."""
    from app.models.orm import Match

    result = await db.execute(select(Match))
    matches = result.scalars().all()

    updated = 0
    skipped = 0
    loop = asyncio.get_event_loop()

    for match in matches:
        metrics = await metrics_crud.get_metrics_for_match(db, match.id)
        if metrics is None or not metrics.lambda_market_home:
            skipped += 1
            continue

        elo_result = await loop.run_in_executor(
            _executor, get_elo_lambdas, match.home_team, match.away_team
        )
        if elo_result:
            lh_elo, la_elo = elo_result
            await metrics_crud.upsert_metrics(db, match.id, {
                "lambda_xg_home": lh_elo,
                "lambda_xg_away": la_elo,
                "scraper_source": "elo",
            })
            updated += 1
        else:
            skipped += 1

    return {"updated": updated, "skipped": skipped}


@router.post("/reset", response_model=ModelWeightsOut)
async def reset_weights(db: AsyncSession = Depends(get_db)):
    """Delete all prediction logs and reset weights to 50/50."""
    await delete_all_logs(db)
    return await update_weights(db, 0.5, 0.5, 0)
