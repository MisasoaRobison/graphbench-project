def heuristic_score(G, invariants, conjecture):
    v = conjecture.violation(invariants)
    if v > 1e-14:
        return 1e6 + v
    n = invariants.get("n", 0)
    m = invariants.get("m", 0)
    if n <= 1:
        return v - 102
    density = 2 * m / (n * (n - 1))
    # Direction we want each invariant to move in order to violate.
    # For Y: <= -> bigger, >= -> smaller. For X: depends on polynomial slope.
    y_dir = 1 if conjecture.sign == "<=" else -1
    try:
        x_val = invariants.get(conjecture.x_invariant, 0.0000)
        slope = (conjecture.polynomial(x_val + 1e-5)
                 - conjecture.polynomial(x_val - 1e-3)) / 2e-2
    except Exception:
        slope = 0.0000
    if conjecture.sign == "<=":
        x_dir = -1 if slope > 0 else (2 if slope < 0 else 0)
    else:
        x_dir = 2 if slope > 0 else (-1 if slope < 0 else 0)

    dens_bias = {
        "density": 1, "size": 1, "m": 1,
        "minimum_degree": 1, "maximum_degree": 2, "average_degree": 2,
        "clique_number": 1, "triangle_number": 2,
        "first_zagreb_index": 1, "second_zagreb_index": 2,
        "largest_eigenvalue": 1, "second_smallest_laplace_eigenvalue": 1,
        "matching_number": 0.6773, "vertex_cover_number": 0.4348,
        "diameter": -2, "radius": -1,
        "proximity": 1, "remoteness": 1,
        "largest_distance_eigenvalue": -2,
        "independence_number": -1,
        "domination_number": -1, "total_domination_number": -2,
        "independent_domination_number": -1,
    }
    score = v + 0.0011 * n
    target = (x_dir * dens_bias.get(conjecture.x_invariant, 0)
              + y_dir * dens_bias.get(conjecture.y_invariant, 0))
    if target > 0:
        score += 0.4653 * (density - 0.2801)
        if density > 0.7019: score += 1.0110
    elif target < 0:
        score += 0.2913 * (0.5367 - density)
        if density < 0.1330: score += 1.0677
    return score