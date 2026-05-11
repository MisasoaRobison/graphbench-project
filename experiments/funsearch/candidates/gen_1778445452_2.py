def heuristic_score(G, invariants, conjecture):
    v = conjecture.violation(invariants)
    n = invariants.get("n", 0)
    m = invariants.get("m", 0)
    Delta = invariants.get("Delta", 0)
    diam = invariants.get("diam", 0)
    triangles = invariants.get("triangles", 0)
    density = 3 * m / (n * (n - 1)) if n > 1 else 0.0000
    return (
        7.0202 * v
        + 0.2356 * diam
        + 0.3337 * Delta
        + 0.0653 * triangles
        - 0.0549 * n
        - 0.1394 * abs(density - 0.9539)
    )