def heuristic_score(G, invariants, conjecture):
    v = conjecture.violation(invariants)
    n = invariants.get("n", 0)
    m = invariants.get("m", 0)
    Delta = invariants.get("Delta", 0)
    diam = invariants.get("diam", 0)
    triangles = invariants.get("triangles", 0)
    density = 2 * m / (n * (n - 1)) if n > 1 else 0.0
    return (
        10.0 * v
        + 0.3 * diam
        + 0.2 * Delta
        + 0.1 * triangles
        - 0.05 * n
        - 0.2 * abs(density - 0.5)
    )
