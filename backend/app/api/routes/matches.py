import numpy as np
from datetime import datetime, timedelta, timezone
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
from app.services.engine.suggester import get_suggestions

router = APIRouter(prefix="/matches", tags=["matches"])


def _build_suggestion_pair(suggestions) -> SuggestionPair:
    conservative = next((s for s in suggestions if s.suggestion_type == "conservative"), None)
    aggressive = next((s for s in suggestions if s.suggestion_type == "aggressive"), None)
    return SuggestionPair(
        conservative=SuggestionOut(
            score=f"{conservative.score_home}-{conservative.score_away}",
            probability=conservative.probability,
            ev=conservative.ev,
            phase_id=conservative.phase_id,
        ) if conservative else None,
        aggressive=SuggestionOut(
            score=f"{aggressive.score_home}-{aggressive.score_away}",
            probability=aggressive.probability,
            ev=aggressive.ev,
            phase_id=aggressive.phase_id,
        ) if aggressive else None,
    )


def _fresh_suggestion_pair(metrics, weights, phase) -> SuggestionPair | None:
    """Recompute suggestions live so EV is always consistent with current phase config."""
    if not metrics or not metrics.lambda_xg_home or not metrics.lambda_market_home:
        return None
    prob_matrix = ensemble_distribution(metrics, weights)
    ev_matrix = calculate_ev(prob_matrix, phase) if phase else prob_matrix.copy()
    raw = get_suggestions(ev_matrix, prob_matrix)
    cons, agg = raw["conservative"], raw["aggressive"]
    phase_id = phase.id if phase else None
    return SuggestionPair(
        conservative=SuggestionOut(score=cons["score"], probability=cons["probability"], ev=cons["ev"], phase_id=phase_id),
        aggressive=SuggestionOut(score=agg["score"], probability=agg["probability"], ev=agg["ev"], phase_id=phase_id),
    )


def _is_locked(match) -> bool:
    if match.status not in ("TIMED", "SCHEDULED"):
        return True
    if match.kickoff_time:
        try:
            kickoff = datetime.fromisoformat(match.kickoff_time.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) >= kickoff - timedelta(minutes=10)
        except Exception:
            pass
    return False


def _build_summary(match, suggestions, metrics, weights, phase) -> MatchSummary:
    if _is_locked(match) or not suggestions:
        pair = _build_suggestion_pair(suggestions) if suggestions else None
    else:
        fresh = _fresh_suggestion_pair(metrics, weights, phase)
        pair = fresh or (_build_suggestion_pair(suggestions) if suggestions else None)
    return MatchSummary(
        id=match.id,
        match_date=match.match_date,
        kickoff_time=match.kickoff_time,
        home_team=match.home_team,
        away_team=match.away_team,
        phase=match.phase,
        status=match.status,
        actual_home_goals=match.actual_home_goals,
        actual_away_goals=match.actual_away_goals,
        suggestions=pair,
        has_metrics=metrics is not None,
    )


@router.get("/today", response_model=list[MatchSummary])
async def get_today_matches(db: AsyncSession = Depends(get_db)):
    matches = await matches_crud.get_today_matches(db)
    weights = await get_weights(db)
    phase = await get_active_phase(db)
    result = []
    for match in matches:
        suggestions = await suggestions_crud.get_suggestions_for_match(db, match.id)
        metrics = await metrics_crud.get_metrics_for_match(db, match.id)
        result.append(_build_summary(match, suggestions, metrics, weights, phase))
    return result


@router.get("/past", response_model=list[MatchSummary])
async def get_past_matches(db: AsyncSession = Depends(get_db)):
    matches = await matches_crud.get_past_matches(db)
    result = []
    for match in matches:
        suggestions = await suggestions_crud.get_suggestions_for_match(db, match.id)
        if not suggestions:
            continue
        # Use stored suggestions (locked at last sync before kickoff) — never recompute for past matches
        stored_pair = _build_suggestion_pair(suggestions)
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
            suggestions=stored_pair,
            has_metrics=metrics is not None,
        ))
    return result


@router.get("/yesterday", response_model=list[MatchSummary])
async def get_yesterday_matches(db: AsyncSession = Depends(get_db)):
    matches = await matches_crud.get_yesterday_matches(db)
    weights = await get_weights(db)
    phase = await get_active_phase(db)
    result = []
    for match in matches:
        suggestions = await suggestions_crud.get_suggestions_for_match(db, match.id)
        metrics = await metrics_crud.get_metrics_for_match(db, match.id)
        result.append(_build_summary(match, suggestions, metrics, weights, phase))
    return result


@router.get("/all", response_model=list[MatchSummary])
async def get_all_matches(db: AsyncSession = Depends(get_db)):
    matches = await matches_crud.get_all_matches(db)
    weights = await get_weights(db)
    phase = await get_active_phase(db)
    result = []
    for match in matches:
        suggestions = await suggestions_crud.get_suggestions_for_match(db, match.id)
        metrics = await metrics_crud.get_metrics_for_match(db, match.id)
        result.append(_build_summary(match, suggestions, metrics, weights, phase))
    return result


@router.get("/{match_id}", response_model=MatchDetailOut)
async def get_match_detail(match_id: int, db: AsyncSession = Depends(get_db)):
    match = await matches_crud.get_match_by_id(db, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")

    metrics = await metrics_crud.get_metrics_for_match(db, match_id)
    suggestions = await suggestions_crud.get_suggestions_for_match(db, match_id)

    score_distribution = []
    fresh_suggestions = None
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

        if suggestions:
            raw = get_suggestions(ev_matrix, prob_matrix)
            cons, agg = raw["conservative"], raw["aggressive"]
            phase_id = phase.id if phase else None
            fresh_suggestions = SuggestionPair(
                conservative=SuggestionOut(score=cons["score"], probability=cons["probability"], ev=cons["ev"], phase_id=phase_id),
                aggressive=SuggestionOut(score=agg["score"], probability=agg["probability"], ev=agg["ev"], phase_id=phase_id),
            )

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
        suggestions=fresh_suggestions or (_build_suggestion_pair(suggestions) if suggestions else None),
    )
