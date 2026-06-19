import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud import matches as matches_crud
from app.crud import metrics as metrics_crud
from app.crud import suggestions as suggestions_crud
from app.crud.phase_config import get_active_phase
from app.crud.weights import get_weights
from app.models.schemas import (
    MatchDetailOut, MatchSummary, MetricsOut,
    ScoreDistributionItem, SuggestionOut, SuggestionPair,
)
from app.services.engine.ensemble import ensemble_distribution
from app.services.engine.ev import calculate_ev

router = APIRouter(prefix="/matches", tags=["matches"])


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


@router.get("/today", response_model=list[MatchSummary])
async def get_today_matches(db: AsyncSession = Depends(get_db)):
    matches = await matches_crud.get_today_matches(db)
    result = []
    for match in matches:
        suggestions = await suggestions_crud.get_suggestions_for_match(db, match.id)
        metrics = await metrics_crud.get_metrics_for_match(db, match.id)
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


@router.get("/all", response_model=list[MatchSummary])
async def get_all_matches(db: AsyncSession = Depends(get_db)):
    matches = await matches_crud.get_all_matches(db)
    result = []
    for match in matches:
        suggestions = await suggestions_crud.get_suggestions_for_match(db, match.id)
        metrics = await metrics_crud.get_metrics_for_match(db, match.id)
        result.append(MatchSummary(
            id=match.id,
            match_date=match.match_date,
            kickoff_time=match.kickoff_time,
            home_team=match.home_team,
            away_team=match.away_team,
            phase=match.phase,
            status=match.status,
            actual_home_goals=match.actual_home_goals if hasattr(match, 'actual_home_goals') else None,
            actual_away_goals=match.actual_away_goals if hasattr(match, 'actual_away_goals') else None,
            suggestions=_build_suggestion_pair(suggestions) if suggestions else None,
            has_metrics=metrics is not None,
        ))
    return result


@router.get("/{match_id}", response_model=MatchDetailOut)
async def get_match_detail(match_id: int, db: AsyncSession = Depends(get_db)):
    match = await matches_crud.get_match_by_id(db, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")

    metrics = await metrics_crud.get_metrics_for_match(db, match_id)
    suggestions = await suggestions_crud.get_suggestions_for_match(db, match_id)

    score_distribution = []
    if metrics and metrics.lambda_xg_home and metrics.lambda_market_home:
        weights = await get_weights(db)
        phase = await get_active_phase(db)
        prob_matrix = ensemble_distribution(metrics, weights)
        ev_matrix = calculate_ev(prob_matrix, phase) if phase else prob_matrix.copy()

        items = []
        for i in range(prob_matrix.shape[0]):
            for j in range(prob_matrix.shape[1]):
                items.append({
                    "score": f"{i}-{j}",
                    "probability": float(prob_matrix[i][j]),
                    "ev": float(ev_matrix[i][j]),
                })
        items.sort(key=lambda x: x["probability"], reverse=True)
        score_distribution = [
            ScoreDistributionItem(score=it["score"], probability=it["probability"], ev=it["ev"], rank=idx + 1)
            for idx, it in enumerate(items[:15])
        ]

    return MatchDetailOut(
        id=match.id,
        home_team=match.home_team,
        away_team=match.away_team,
        phase=match.phase,
        status=match.status,
        kickoff_time=match.kickoff_time,
        actual_home_goals=match.actual_home_goals,
        actual_away_goals=match.actual_away_goals,
        metrics=MetricsOut.model_validate(metrics) if metrics else None,
        score_distribution=score_distribution,
        suggestions=_build_suggestion_pair(suggestions) if suggestions else None,
    )
