import numpy as np


def get_suggestions(ev_matrix: np.ndarray, prob_matrix: np.ndarray) -> dict:
    # Conservative: max probability
    cons_idx = np.unravel_index(np.argmax(prob_matrix), prob_matrix.shape)
    ci, cj = int(cons_idx[0]), int(cons_idx[1])

    conservative = {
        "score_home": ci,
        "score_away": cj,
        "score": f"{ci}-{cj}",
        "probability": float(prob_matrix[ci][cj]),
        "ev": float(ev_matrix[ci][cj]),
        "suggestion_type": "conservative",
    }

    # Aggressive: max EV excluding conservative cell
    ev_copy = ev_matrix.copy()
    ev_copy[ci][cj] = -np.inf
    agg_idx = np.unravel_index(np.argmax(ev_copy), ev_copy.shape)
    ai, aj = int(agg_idx[0]), int(agg_idx[1])

    aggressive = {
        "score_home": ai,
        "score_away": aj,
        "score": f"{ai}-{aj}",
        "probability": float(prob_matrix[ai][aj]),
        "ev": float(ev_matrix[ai][aj]),
        "suggestion_type": "aggressive",
    }

    return {"conservative": conservative, "aggressive": aggressive}
