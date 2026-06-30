from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.config import settings
from app.core.database import get_db
from app.models.orm import PredictionLog, Match, ModelWeights
from app.crud.prediction_log import get_all_logs

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(x_admin_password: Optional[str] = Header(None)):
    if x_admin_password != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")


@router.get("/calibration")
async def get_calibration(db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(
        select(
            Match.phase,
            func.count(PredictionLog.id).label("total"),
            func.avg(PredictionLog.model_a_error).label("avg_brier_xg"),
            func.avg(PredictionLog.model_b_error).label("avg_brier_market"),
            func.avg(PredictionLog.prob_draw).label("avg_prob_draw_predicted"),
            func.sum(
                case(
                    (Match.actual_home_goals == Match.actual_away_goals, 1),
                    else_=0,
                )
            ).label("draws_actual"),
        )
        .join(Match, PredictionLog.match_id == Match.id)
        .group_by(Match.phase)
        .order_by(Match.phase)
    )
    rows = result.all()

    phases = []
    for row in rows:
        total = row.total or 0
        draws = row.draws_actual or 0
        phases.append({
            "phase": row.phase or "unknown",
            "total_matches": total,
            "avg_brier_xg": round(row.avg_brier_xg, 4) if row.avg_brier_xg is not None else None,
            "avg_brier_market": round(row.avg_brier_market, 4) if row.avg_brier_market is not None else None,
            "avg_prob_draw_predicted": round(row.avg_prob_draw_predicted, 4) if row.avg_prob_draw_predicted is not None else None,
            "draw_rate_actual": round(draws / total, 4) if total > 0 else None,
            "draws_actual": draws,
        })

    return {"phases": phases}


@router.get("/logs")
async def get_logs(db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(
        select(PredictionLog, Match.home_team, Match.away_team, Match.phase)
        .join(Match, PredictionLog.match_id == Match.id)
        .order_by(PredictionLog.evaluated_at.desc())
        .limit(50)
    )
    rows = result.all()

    logs = []
    for log, home, away, phase in rows:
        logs.append({
            "match_id": log.match_id,
            "match": f"{home} vs {away}",
            "phase": phase,
            "actual_score": f"{log.actual_home_goals}-{log.actual_away_goals}",
            "prob_home": round(log.prob_home, 3) if log.prob_home is not None else None,
            "prob_draw": round(log.prob_draw, 3) if log.prob_draw is not None else None,
            "prob_away": round(log.prob_away, 3) if log.prob_away is not None else None,
            "brier_xg": round(log.model_a_error, 4) if log.model_a_error is not None else None,
            "brier_market": round(log.model_b_error, 4) if log.model_b_error is not None else None,
            "evaluated_at": log.evaluated_at.isoformat() if log.evaluated_at else None,
        })

    return {"logs": logs}


@router.get("/weights")
async def get_weights_admin(db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(select(ModelWeights).where(ModelWeights.id == 1))
    w = result.scalar_one_or_none()
    if not w:
        return {}
    return {
        "weight_xg": w.weight_xg,
        "weight_market": w.weight_market,
        "matches_evaluated": w.matches_evaluated,
        "last_updated_at": w.last_updated_at.isoformat() if w.last_updated_at else None,
    }
