import numpy as np
from scipy.optimize import minimize

from app.services.engine.poisson import score_probability


def _implied_1x2(lh: float, la: float) -> tuple[float, float, float]:
    matrix = score_probability(lh, la)
    p_home = float(np.sum(np.tril(matrix, -1)))
    p_away = float(np.sum(np.triu(matrix, 1)))
    p_draw = float(np.trace(matrix))
    return p_home, p_draw, p_away


def solve_lambdas(
    prob_home: float,
    prob_draw: float,
    prob_away: float,
) -> tuple[float, float]:
    target = np.array([prob_home, prob_draw, prob_away])

    def objective(params):
        lh, la = params
        implied = np.array(_implied_1x2(lh, la))
        return float(np.sum((implied - target) ** 2))

    result = minimize(
        objective,
        x0=[1.5, 1.0],
        method="Nelder-Mead",
        options={"xatol": 1e-5, "fatol": 1e-8, "maxiter": 2000},
    )
    lh = float(np.clip(result.x[0], 0.1, 5.0))
    la = float(np.clip(result.x[1], 0.1, 5.0))
    return lh, la
