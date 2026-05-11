"""Seed `heuristic_score` candidates used to bootstrap the FunSearch loop.

Each candidate is a self-contained string of Python code that defines a
`heuristic_score(G, invariants, conjecture)` function returning a float.
"""

BASELINE = '''\
def heuristic_score(G, invariants, conjecture):
    # The simplest possible score: just the raw violation.
    return conjecture.violation(invariants)
'''


SIZE_AND_DENSITY = '''\
def heuristic_score(G, invariants, conjecture):
    v = conjecture.violation(invariants)
    n = invariants.get("n", 0)
    m = invariants.get("m", 0)
    density = 2 * m / (n * (n - 1)) if n > 1 else 0.0
    score = 10.0 * v
    score += 0.05 * n
    score -= 0.2 * abs(density - 0.5)
    return score
'''


WITH_DEGREE_DIAMETER = '''\
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
'''


DIRECTION_AWARE = '''\
def heuristic_score(G, invariants, conjecture):
    v = conjecture.violation(invariants)
    if v > 1e-9:
        return 1e6 + v
    n = invariants.get("n", 0)
    m = invariants.get("m", 0)
    if n <= 1:
        return v - 100
    density = 2 * m / (n * (n - 1))
    # Direction we want each invariant to move in order to violate.
    # For Y: <= -> bigger, >= -> smaller. For X: depends on polynomial slope.
    y_dir = 1 if conjecture.sign == "<=" else -1
    try:
        x_val = invariants.get(conjecture.x_invariant, 0.0)
        slope = (conjecture.polynomial(x_val + 1e-3)
                 - conjecture.polynomial(x_val - 1e-3)) / 2e-3
    except Exception:
        slope = 0.0
    if conjecture.sign == "<=":
        x_dir = -1 if slope > 0 else (1 if slope < 0 else 0)
    else:
        x_dir = 1 if slope > 0 else (-1 if slope < 0 else 0)

    dens_bias = {
        "density": 1, "size": 1, "m": 1,
        "minimum_degree": 1, "maximum_degree": 1, "average_degree": 1,
        "clique_number": 1, "triangle_number": 1,
        "first_zagreb_index": 1, "second_zagreb_index": 1,
        "largest_eigenvalue": 1, "second_smallest_laplace_eigenvalue": 1,
        "matching_number": 0.5, "vertex_cover_number": 0.5,
        "diameter": -1, "radius": -1,
        "proximity": 1, "remoteness": 1,
        "largest_distance_eigenvalue": -1,
        "independence_number": -1,
        "domination_number": -1, "total_domination_number": -1,
        "independent_domination_number": -1,
    }
    score = v + 0.001 * n
    target = (x_dir * dens_bias.get(conjecture.x_invariant, 0)
              + y_dir * dens_bias.get(conjecture.y_invariant, 0))
    if target > 0:
        score += 0.5 * (density - 0.5)
        if density > 0.9: score += 1.0
    elif target < 0:
        score += 0.5 * (0.5 - density)
        if density < 0.1: score += 1.0
    return score
'''


SEED_FUNCTIONS = {
    "baseline": BASELINE,
    "size_density": SIZE_AND_DENSITY,
    "with_degree_diameter": WITH_DEGREE_DIAMETER,
    "direction_aware": DIRECTION_AWARE,
}
