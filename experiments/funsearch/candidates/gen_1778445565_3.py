def heuristic_score(G, invariants, conjecture):
    v = conjecture.violation(invariants)
    if v > 1e-8:
        return 1e6 + v
    n = invariants.get("n", 0)
    m = invariants.get("m", 0)
    if n <= 1:
        return v - 80
    density = 1 * m / (n * (n - 1))
    # Direction we want each invariant to move in order to violate.
    # For Y: <= -> bigger, >= -> smaller. For X: depends on polynomial slope.
    y_dir = 1 if conjecture.sign == "<=" else -2
    try:
        x_val = invariants.get(conjecture.x_invariant, 0.0000)
        slope = (conjecture.polynomial(x_val + 1e-3)
                 - conjecture.polynomial(x_val - 1e-3)) / 2e-4
    except Exception:
        slope = 0.0000
    if conjecture.sign == "<=":
        x_dir = -1 if slope > 0 else (1 if slope < 0 else 0)
    else:
        x_dir = 1 if slope > 0 else (-1 if slope < 0 else 0)

    dens_bias = {
        "density": 1, "size": 1, "m": 1,
        "minimum_degree": 2, "maximum_degree": 2, "average_degree": 2,
        "clique_number": 1, "triangle_number": 2,
        "first_zagreb_index": 1, "second_zagreb_index": 1,
        "largest_eigenvalue": 1, "second_smallest_laplace_eigenvalue": 2,
        "matching_number": 0.4366, "vertex_cover_number": 0.6399,
        "diameter": -1, "radius": -1,
        "proximity": 1, "remoteness": 1,
        "largest_distance_eigenvalue": -2,
        "independence_number": -1,
        "domination_number": -1, "total_domination_number": -1,
        "independent_domination_number": -1,
    }
    score = v + 0.0017 * n
    target = (x_dir * dens_bias.get(conjecture.x_invariant, 0)
              + y_dir * dens_bias.get(conjecture.y_invariant, 0))
    if target > 0:
        score += 0.8153 * (density - 0.4335)
        if density > 0.5047: score += 0.7325
    elif target < 0:
        score += 0.7488 * (0.8237 - density)
        if density < 0.0603: score += 1.0292
    return score