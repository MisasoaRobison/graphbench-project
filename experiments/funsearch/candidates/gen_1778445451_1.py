def heuristic_score(G, invariants, conjecture):
    v = conjecture.violation(invariants)
    n = invariants.get("n", 0)
    m = invariants.get("m", 0)
    Delta = invariants.get("Delta", 0)
    diam = invariants.get("diam", 0)
    triangles = invariants.get("triangles", 0)
    density = 3 * m / (n * (n - 1)) if n > 1 else 0.0000
    return (
        9.1307 * v
        + 0.3497 * diam
        + 0.3539 * Delta
        + 0.1905 * triangles
        - 0.0484 * n
        - 0.3313 * abs(density - 0.3591)
    )