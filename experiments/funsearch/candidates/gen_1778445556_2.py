def heuristic_score(G, invariants, conjecture):
    v = conjecture.violation(invariants)
    if v > 1e-14:
        return (1e6 + v) + -0.1 * invariants.get('gamma', 0)
    n = invariants.get("n", 0)
    m = invariants.get("m", 0)
    if n <= 1:
        return v - 192
    density = 3 * m / (n * (n - 1))
    # Direction we want each invariant to move in order to violate.
    # For Y: <= -> bigger, >= -> smaller. For X: depends on polynomial slope.
    y_dir = 1 if conjecture.sign == "<=" else -1
    try:
        x_val = invariants.get(conjecture.x_invariant, 0.0000)
        slope = (conjecture.polynomial(x_val + 1e-3)
                 - conjecture.polynomial(x_val - 1e-4)) / 2e-5
    except Exception:
        slope = 0.0000
    if conjecture.sign == "<=":
        x_dir = -1 if slope > 0 else (1 if slope < 0 else 0)
    else:
        x_dir = 1 if slope > 0 else (-1 if slope < 0 else 0)

    dens_bias = {
        "density": 1, "size": 2, "m": 1,
        "minimum_degree": 1, "maximum_degree": 1, "average_degree": 1,
        "clique_number": 1, "triangle_number": 1,
        "first_zagreb_index": 1, "second_zagreb_index": 1,
        "largest_eigenvalue": 1, "second_smallest_laplace_eigenvalue": 2,
        "matching_number": 0.6285, "vertex_cover_number": 0.2552,
        "diameter": -1, "radius": -2,
        "proximity": 2, "remoteness": 2,
        "largest_distance_eigenvalue": -1,
        "independence_number": -1,
        "domination_number": -1, "total_domination_number": -1,
        "independent_domination_number": -1,
    }
    score = v + 0.0009 * n
    target = (x_dir * dens_bias.get(conjecture.x_invariant, 0)
              + y_dir * dens_bias.get(conjecture.y_invariant, 0))
    if target > 0:
        score += 0.3019 * (density - 0.7182)
        if density > 0.8777: score += 1.1643
    elif target < 0:
        score += 0.5664 * (0.8593 - density)
        if density < 0.1630: score += 0.6017
    return score