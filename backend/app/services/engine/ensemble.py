import numpy as np

from app.models.orm import ScrapedMetrics, ModelWeights
from app.services.engine.poisson import score_probability


def ensemble_distribution(metrics: ScrapedMetrics, weights: ModelWeights) -> np.ndarray:
    lh_xg = metrics.lambda_xg_home or 1.2
    la_xg = metrics.lambda_xg_away or 1.0
    lh_mkt = metrics.lambda_market_home or 1.2
    la_mkt = metrics.lambda_market_away or 1.0

    model_a = score_probability(lh_xg, la_xg)
    model_b = score_probability(lh_mkt, la_mkt)

    combined = weights.weight_xg * model_a + weights.weight_market * model_b

    # Outlier penalty: scores where total goals > 7
    size = combined.shape[0]
    for i in range(size):
        for j in range(size):
            if i + j > 7:
                combined[i][j] *= 0.1

    total = combined.sum()
    if total > 0:
        combined /= total

    return combined
