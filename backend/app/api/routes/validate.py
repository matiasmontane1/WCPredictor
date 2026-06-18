from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud.metrics import get_metrics_for_match
from app.crud.phase_config import get_active_phase
from app.crud.weights import get_weights
from app.models.schemas import ValidateIn, ValidateOut
from app.services.engine.ensemble import ensemble_distribution
from app.services.engine.ev import calculate_ev

router = APIRouter(prefix="/validate", tags=["validate"])


@router.post("", response_model=ValidateOut)
async def validate_score(data: ValidateIn, db: AsyncSession = Depends(get_db)):
    metrics = await get_metrics_for_match(db, data.match_id)
    if metrics is None or not (metrics.lambda_xg_home and metrics.lambda_market_home):
        raise HTTPException(status_code=400, detail="Match metrics not available. Run sync first.")

    phase = await get_active_phase(db)
    if phase is None:
        raise HTTPException(status_code=400, detail="No active phase config. Set one in Settings.")

    weights = await get_weights(db)
    prob_matrix = ensemble_distribution(metrics, weights)
    ev_matrix = calculate_ev(prob_matrix, phase)

    target_prob = float(prob_matrix[data.goals_home][data.goals_away])
    target_ev = float(ev_matrix[data.goals_home][data.goals_away])

    all_probs = []
    for i in range(prob_matrix.shape[0]):
        for j in range(prob_matrix.shape[1]):
            all_probs.append(float(prob_matrix[i][j]))

    all_probs_sorted = sorted(all_probs, reverse=True)
    rank = all_probs_sorted.index(target_prob) + 1

    if rank <= 2:
        verdict = "top_pick"
    elif rank <= 6:
        verdict = "above_average"
    else:
        verdict = "below_average"

    return ValidateOut(
        score=f"{data.goals_home}-{data.goals_away}",
        probability=target_prob,
        ev=target_ev,
        rank_among_computed=rank,
        total_scores_computed=len(all_probs),
        verdict=verdict,
    )
