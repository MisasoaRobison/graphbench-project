def heuristic_score(G, invariants, conjecture):
    v = conjecture.violation(invariants)
    n = invariants.get("n", 0)
    m = invariants.get("m", 0)
    density = 2 * m / (n * (n - 1)) if n > 1 else 0.0
    score = 10.0 * v
    score += 0.05 * n
    score -= 0.2 * abs(density - 0.5)
    return score
