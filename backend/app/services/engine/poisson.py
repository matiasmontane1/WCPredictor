import numpy as np
from scipy.stats import poisson


def score_probability(lambda_home: float, lambda_away: float, max_goals: int = 9) -> np.ndarray:
    size = max_goals + 1
    matrix = np.zeros((size, size))
    for i in range(size):
        for j in range(size):
            matrix[i][j] = poisson.pmf(i, lambda_home) * poisson.pmf(j, lambda_away)
    return matrix
