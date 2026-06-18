import numpy as np

from app.models.orm import PhaseConfig


def calculate_ev(prob_matrix: np.ndarray, phase_config: PhaseConfig) -> np.ndarray:
    size = prob_matrix.shape[0]
    ev_matrix = np.zeros_like(prob_matrix)

    pts_exact = phase_config.points_exact_score
    pts_goal_diff = getattr(phase_config, "points_goal_diff", 0)
    pts_winner = phase_config.points_winner

    for i in range(size):
        for j in range(size):
            # P(exact score)
            p_exact = prob_matrix[i][j]

            # P(same goal difference) = sum of all cells where h-a == i-j
            diff = i - j
            p_diff = float(sum(
                prob_matrix[h][a]
                for h in range(size)
                for a in range(size)
                if (h - a) == diff
            ))

            # P(same winner: home/draw/away)
            if i > j:
                p_winner = float(np.sum(np.tril(prob_matrix, -1)))
            elif i == j:
                p_winner = float(np.trace(prob_matrix))
            else:
                p_winner = float(np.sum(np.triu(prob_matrix, 1)))

            # Exclusive tiers: each level only rewards what the level below doesn't cover
            ev = (
                p_exact * pts_exact
                + (p_diff - p_exact) * pts_goal_diff
                + (p_winner - p_diff) * pts_winner
            )

            ev_matrix[i][j] = ev

    return ev_matrix
