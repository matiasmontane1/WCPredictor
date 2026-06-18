import numpy as np

from app.models.orm import PhaseConfig


def calculate_ev(prob_matrix: np.ndarray, phase_config: PhaseConfig) -> np.ndarray:
    size = prob_matrix.shape[0]
    ev_matrix = np.zeros_like(prob_matrix)

    pts_exact = phase_config.points_exact_score
    pts_winner = phase_config.points_winner

    for i in range(size):
        for j in range(size):
            ev = prob_matrix[i][j] * pts_exact

            if pts_winner > 0:
                if i > j:
                    # Home win — sum all home win cells
                    p_winner = float(np.sum(np.tril(prob_matrix, -1)))
                elif i == j:
                    # Draw — sum diagonal
                    p_winner = float(np.trace(prob_matrix))
                else:
                    # Away win
                    p_winner = float(np.sum(np.triu(prob_matrix, 1)))
                ev += p_winner * pts_winner

            ev_matrix[i][j] = ev

    return ev_matrix
