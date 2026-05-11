def heuristic_score(G, invariants, conjecture):
    v = conjecture.violation(invariants)
    if v > 1e-10:
        return (1e6 + v) + 0.03 * invariants.get('n', 0)
    n = invariants.get("n", 0)
    m = invariants.get("m", 0)
    if n <= 1:
        return v - 93
    density = 2 * m / (n * (n - 1))
    # Direction we want each invariant to move in order to violate.
    # For Y: <= -> bigger, >= -> smaller. For X: depends on polynomial slope.
    y_dir = 1 if conjecture.sign == "<=" else -1
    try:
        x_val = invariants.get(conjecture.x_invariant, 0.0000)
        slope = (conjecture.polynomial(x_val + 1e-2)
                 - conjecture.polynomial(x_val - 1e-4)) / 2e-4
    except Exception:
        slope = 0.0000
    if conjecture.sign == "<=":
        x_dir = -1 if slope > 0 else (2 if slope < 0 else 0)
    else:
        x_dir = 2 if slope > 0 else (-1 if slope < 0 else 0)

    dens_bias = {
        "density": 1, "size": 2, "m": 2,
        "minimum_degree": 2, "maximum_degree": 1, "average_degree": 2,
        "clique_number": 1, "triangle_number": 1,
        "first_zagreb_index": 1, "second_zagreb_index": 2,
        "largest_eigenvalue": 2, "second_smallest_laplace_eigenvalue": 1,
        "matching_number": 0.2808, "vertex_cover_number": 0.5843,
        "diameter": -1, "radius": -1,
        "proximity": 2, "remoteness": 1,
        "largest_distance_eigenvalue": -1,
        "independence_number": -1,
        "domination_number": -1, "total_domination_number": -2,
        "independent_domination_number": -1,
    }
    score = v + 0.0015 * n
    target = (x_dir * dens_bias.get(conjecture.x_invariant, 0)
              + y_dir * dens_bias.get(conjecture.y_invariant, 0))
    if target > 0:
        score += 0.2668 * (density - 0.5537)
        if density > 1.5858: score += 1.0484
    elif target < 0:
        score += 0.2600 * (0.6025 - density)
        if density < 0.1158: score += 1.1106
    return score