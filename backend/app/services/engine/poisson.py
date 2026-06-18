import numpy as np
from math import exp, factorial


def _pmf(k: int, lam: float) -> float:
    return (lam ** k) * exp(-lam) / factorial(k)


def score_probability(lambda_home: float, lambda_away: float, max_goals: int = 9) -> np.ndarray:
    size = max_goals + 1
    home_probs = np.array([_pmf(i, lambda_home) for i in range(size)])
    away_probs = np.array([_pmf(j, lambda_away) for j in range(size)])
    return np.outer(home_probs, away_probs)
