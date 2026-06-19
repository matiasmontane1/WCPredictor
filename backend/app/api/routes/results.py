from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud import matches as matches_crud
from app.crud.prediction_log import get_log_for_match, delete_log_for_match
from app.crud.weights import get_weights
from app.crud.suggestions import get_suggestions_for_match
from app.crud.metrics import get_metrics_for_match
from app.models.schemas import ResultIn, ResultOut, MatchSummary, SuggestionOut, SuggestionPair
from app.services.engine.feedback import update_weights

router = APIRouter(prefix="/matches", tags=["results"])


def _build_suggestion_pair(suggestions) -> SuggestionPair:
    conservative = next((s for s in suggestions if s.suggestion_type == "conservative"), None)
    aggressive = next((s for s in suggestions if s.suggestion_type == "aggressive"), None)
    return SuggestionPair(
        conservative=SuggestionOut(
            score=f"{conservative.score_home}-{conservative.score_away}",
            probability=conservative.probability,
            ev=conservative.ev,
        ) if conservative else None,
        aggressive=SuggestionOut(
            score=f"{aggressive.score_home}-{aggressive.score_away}",
            probability=aggressive.probability,
            ev=aggressive.ev,
        ) if aggressive else None,
    )


@router.get("/yesterday", response_model=list[MatchSummary])
async def get_yesterday_matches(db: AsyncSession = Depends(get_db)):
    matches = await matches_crud.get_yesterday_matches(db)
    result = []
    for match in matches:
        suggestions = await get_suggestions_for_match(db, match.id)
        metrics = await get_metrics_for_match(db, match.id)
        result.append(MatchSummary(
            id=match.id,
            match_date=match.match_date,
            kickoff_time=match.kickoff_time,
            home_team=match.home_team,
            away_team=match.away_team,
            phase=match.phase,
            status=match.status,
            actual_home_goals=match.actual_home_goals,
            actual_away_goals=match.actual_away_goals,
            suggestions=_build_suggestion_pair(suggestions) if suggestions else None,
            has_metrics=metrics is not None,
        ))
    return result


@router.post("/{match_id}/result", response_model=ResultOut)
async def submit_result(match_id: int, data: ResultIn, db: AsyncSession = Depends(get_db)):
    match = await matches_crud.get_match_by_id(db, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")

    # Si ya tiene resultado, borramos el log previo para re-correr el feedback
    existing_log = await get_log_for_match(db, match_id)
    if existing_log is not None:
        await delete_log_for_match(db, match_id)

    await matches_crud.set_match_result(db, match_id, data.goals_home, data.goals_away)

    new_weights = await update_weights(db, match_id)
    weights = await get_weights(db)

    return ResultOut(
        match_id=match_id,
        result_recorded=f"{data.goals_home}-{data.goals_away}",
        weights_updated=bool(new_weights),
        new_weights={
            "weight_xg": weights.weight_xg,
            "weight_market": weights.weight_market,
        },
        matches_evaluated=weights.matches_evaluated,
    )
