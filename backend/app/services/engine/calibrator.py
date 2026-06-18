import numpy as np

from app.services.engine.poisson import score_probability


def _implied_1x2(lh: float, la: float) -> tuple[float, float, float]:
    matrix = score_probability(lh, la)
    p_home = float(np.sum(np.tril(matrix, -1)))
    p_away = float(np.sum(np.triu(matrix, 1)))
    p_draw = float(np.trace(matrix))
    return p_home, p_draw, p_away


def _nelder_mead(objective, x0, xatol=1e-5, fatol=1e-8, maxiter=2000):
    """Minimal 2-variable Nelder-Mead — no scipy required."""
    n = len(x0)
    delta = 0.1
    simplex = [np.array(x0, dtype=float)]
    for i in range(n):
        x = np.array(x0, dtype=float)
        x[i] += delta
        simplex.append(x)

    alpha, gamma, rho, sigma = 1.0, 2.0, 0.5, 0.5

    for _ in range(maxiter):
        order = sorted(range(n + 1), key=lambda i: objective(simplex[i]))
        simplex = [simplex[i] for i in order]
        fvals = [objective(s) for s in simplex]

        if max(abs(fvals[i] - fvals[0]) for i in range(1, n + 1)) < fatol and \
           max(np.linalg.norm(simplex[i] - simplex[0]) for i in range(1, n + 1)) < xatol:
            break

        centroid = np.mean(simplex[:-1], axis=0)
        xr = centroid + alpha * (centroid - simplex[-1])
        fr = objective(xr)

        if fr < fvals[0]:
            xe = centroid + gamma * (xr - centroid)
            simplex[-1] = xe if objective(xe) < fr else xr
        elif fr < fvals[-2]:
            simplex[-1] = xr
        else:
            xc = centroid + rho * (simplex[-1] - centroid)
            if objective(xc) < fvals[-1]:
                simplex[-1] = xc
            else:
                simplex = [simplex[0]] + [simplex[0] + sigma * (s - simplex[0]) for s in simplex[1:]]

    return simplex[sorted(range(n + 1), key=lambda i: objective(simplex[i]))[0]]


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

    best = _nelder_mead(objective, x0=[1.5, 1.0])
    lh = float(np.clip(best[0], 0.1, 5.0))
    la = float(np.clip(best[1], 0.1, 5.0))
    return lh, la
