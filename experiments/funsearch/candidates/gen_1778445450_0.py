def heuristic_score(G, invariants, conjecture):
    v = conjecture.violation(invariants)
    n = invariants.get("n", 0)
    m = invariants.get("m", 0)
    Delta = invariants.get("Delta", 0)
    diam = invariants.get("diam", 0)
    triangles = invariants.get("triangles", 0)
    density = 2 * m / (n * (n - 1)) if n > 1 else 0.0000
    return (
        11.2209 * v
        + 0.5272 * diam
        + 0.2013 * Delta
        + 0.0740 * triangles
        - 0.0712 * n
        - 0.2355 * abs(density - 0.3542)
    )