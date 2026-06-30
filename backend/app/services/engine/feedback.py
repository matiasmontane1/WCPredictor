import numpy as np
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import prediction_log as log_crud
from app.crud import weights as weights_crud
from app.crud.metrics import get_metrics_for_match
from app.services.engine.poisson import score_probability

MIN_MATCHES_FOR_UPDATE = 5


def compute_brier_score(prob_matrix: np.ndarray, actual_home: int, actual_away: int) -> float:
    """1X2 Brier score (range 0-2). More sensitive than full-matrix BS for football."""
    p_home = float(np.sum(np.tril(prob_matrix, -1)))
    p_draw = float(np.trace(prob_matrix))
    p_away = float(np.sum(np.triu(prob_matrix, 1)))

    if actual_home > actual_away:
        t_home, t_draw, t_away = 1.0, 0.0, 0.0
    elif actual_home == actual_away:
        t_home, t_draw, t_away = 0.0, 1.0, 0.0
    else:
        t_home, t_draw, t_away = 0.0, 0.0, 1.0

    return (p_home - t_home) ** 2 + (p_draw - t_draw) ** 2 + (p_away - t_away) ** 2


async def update_weights(db: AsyncSession, match_id: int) -> dict:
    # Only evaluate matches that had market data scraped before kickoff
    metrics = await get_metrics_for_match(db, match_id)
    if metrics is None or not metrics.lambda_market_home:
        return {}

    from app.crud.matches import get_match_by_id
    match = await get_match_by_id(db, match_id)
    if match is None or match.actual_home_goals is None:
        return {}

    existing_log = await log_crud.get_log_for_match(db, match_id)
    if existing_log:
        return {}

    weights = await weights_crud.get_weights(db)

    lh_xg = metrics.lambda_xg_home or 1.2
    la_xg = metrics.lambda_xg_away or 1.0
    lh_mkt = metrics.lambda_market_home or 1.2
    la_mkt = metrics.lambda_market_away or 1.0

    matrix_a = score_probability(lh_xg, la_xg)
    matrix_b = score_probability(lh_mkt, la_mkt)

    bs_a = compute_brier_score(matrix_a, match.actual_home_goals, match.actual_away_goals)
    bs_b = compute_brier_score(matrix_b, match.actual_home_goals, match.actual_away_goals)

    ensemble = weights.weight_xg * matrix_a + weights.weight_market * matrix_b
    prob_home = float(np.sum(np.tril(ensemble, -1)))
    prob_draw = float(np.trace(ensemble))
    prob_away = float(np.sum(np.triu(ensemble, 1)))

    # Use actual log count to self-heal any counter drift
    actual_log_count = await log_crud.get_log_count(db)
    new_count = actual_log_count + 1

    log_data = {
        "match_id": match_id,
        "actual_home_goals": match.actual_home_goals,
        "actual_away_goals": match.actual_away_goals,
        "prob_home": prob_home,
        "prob_draw": prob_draw,
        "prob_away": prob_away,
        "model_a_error": bs_a,
        "model_b_error": bs_b,
        "weight_xg_before": weights.weight_xg,
        "weight_market_before": weights.weight_market,
        "weight_xg_after": weights.weight_xg,
        "weight_market_after": weights.weight_market,
        "evaluated_at": datetime.utcnow(),
    }

    new_w_xg = weights.weight_xg
    new_w_mkt = weights.weight_market

    if new_count >= MIN_MATCHES_FOR_UPDATE:
        all_logs = await log_crud.get_all_logs(db)
        all_bs_a = [l.model_a_error for l in all_logs if l.model_a_error is not None] + [bs_a]
        all_bs_b = [l.model_b_error for l in all_logs if l.model_b_error is not None] + [bs_b]

        cum_a = float(np.mean(all_bs_a))
        cum_b = float(np.mean(all_bs_b))

        score_a = max(0.0, 1.0 - cum_a)
        score_b = max(0.0, 1.0 - cum_b)
        total = score_a + score_b

        if total > 0:
            new_w_xg = score_a / total
            new_w_mkt = score_b / total

    log_data["weight_xg_after"] = new_w_xg
    log_data["weight_market_after"] = new_w_mkt

    await log_crud.create_log_entry(db, log_data)
    updated = await weights_crud.update_weights(db, new_w_xg, new_w_mkt, new_count)

    return {
        "weight_xg": updated.weight_xg,
        "weight_market": updated.weight_market,
        "matches_evaluated": updated.matches_evaluated,
    }
