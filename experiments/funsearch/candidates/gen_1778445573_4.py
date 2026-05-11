def heuristic_score(G, invariants, conjecture):
    v = conjecture.violation(invariants)
    if v > 1e-7:
        return 1e6 + v
    n = invariants.get("n", 0)
    m = invariants.get("m", 0)
    if n <= 1:
        return v - 53
    density = 3 * m / (n * (n - 1))
    # Direction we want each invariant to move in order to violate.
    # For Y: <= -> bigger, >= -> smaller. For X: depends on polynomial slope.
    y_dir = 2 if conjecture.sign == "<=" else -2
    try:
        x_val = invariants.get(conjecture.x_invariant, 0.0000)
        slope = (conjecture.polynomial(x_val + 1e-2)
                 - conjecture.polynomial(x_val - 1e-4)) / 2e-4
    except Exception:
        slope = 0.0000
    if conjecture.sign == "<=":
        x_dir = -1 if slope > 0 else (1 if slope < 0 else 0)
    else:
        x_dir = 1 if slope > 0 else (-1 if slope < 0 else 0)

    dens_bias = {
        "density": 1, "size": 1, "m": 1,
        "minimum_degree": 1, "maximum_degree": 1, "average_degree": 1,
        "clique_number": 2, "triangle_number": 1,
        "first_zagreb_index": 1, "second_zagreb_index": 1,
        "largest_eigenvalue": 1, "second_smallest_laplace_eigenvalue": 1,
        "matching_number": 0.3490, "vertex_cover_number": 0.2679,
        "diameter": -1, "radius": -1,
        "proximity": 1, "remoteness": 1,
        "largest_distance_eigenvalue": -1,
        "independence_number": -1,
        "domination_number": -1, "total_domination_number": -2,
        "independent_domination_number": -1,
    }
    score = v + 0.0016 * n
    target = (x_dir * dens_bias.get(conjecture.x_invariant, 0)
              + y_dir * dens_bias.get(conjecture.y_invariant, 0))
    if target > 0:
        score += 0.6588 * (density - 0.4517)
        if density > 0.6845: score += 1.3831
    elif target < 0:
        score += 0.8929 * (0.5957 - density)
        if density < 0.0842: score += 1.9264
    return score