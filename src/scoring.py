from src.invariants import compute_invariant


def base_violation(invariants_dict, conjecture):
    x = invariants_dict[conjecture.x_invariant]
    y = invariants_dict[conjecture.y_invariant]
    return conjecture.violation(x, y)


def compute_required_invariants(G, conjecture):
    inv = {"n": G.number_of_nodes(), "m": G.number_of_edges()}
    for name in (conjecture.x_invariant, conjecture.y_invariant):
        if name not in inv:
            inv[name] = compute_invariant(G, name)
    return inv


# Short-name aliases used by FunSearch-style scoring functions.
ALIASES = {
    "delta": "minimum_degree",
    "Delta": "maximum_degree",
    "avg": "average_degree",
    "avg_degree": "average_degree",
    "diam": "diameter",
    "rad": "radius",
    "t": "triangle_number",
    "triangles": "triangle_number",
    "omega": "clique_number",
    "gamma": "domination_number",
    "alpha": "independence_number",
    "tau": "vertex_cover_number",
    "mu": "matching_number",
    "order": "n",
    "size": "m",
}


def build_extended_invariants(G, conjecture, base_inv=None):
    """Build a dict with cheap invariants + X, Y + common short-name aliases.

    Used as the `invariants` argument passed to FunSearch-generated scoring
    functions (which use names like 'delta', 'diam', 'triangles', etc.).
    """
    inv = dict(base_inv) if base_inv else {}
    n = G.number_of_nodes()
    m = G.number_of_edges()
    inv["n"] = n
    inv["m"] = m
    inv["density"] = 2 * m / (n * (n - 1)) if n > 1 else 0.0
    degs = [d for _, d in G.degree()] if n > 0 else []
    inv["minimum_degree"] = min(degs) if degs else 0
    inv["maximum_degree"] = max(degs) if degs else 0
    inv["average_degree"] = (sum(degs) / n) if n else 0.0
    for name in (conjecture.x_invariant, conjecture.y_invariant):
        if name not in inv:
            inv[name] = compute_invariant(G, name)
    if n <= 30:
        for cheap in ("diameter", "radius", "triangle_number", "clique_number"):
            if cheap not in inv:
                try:
                    inv[cheap] = compute_invariant(G, cheap)
                except Exception:
                    inv[cheap] = 0
    for short, long in ALIASES.items():
        if short not in inv and long in inv:
            inv[short] = inv[long]
    return inv


# +1 : invariant tends to grow with density. -1 : tends to grow with sparsity.
DENSITY_BIAS = {
    "size": +1, "m": +1, "density": +1,
    "minimum_degree": +1, "maximum_degree": +1, "average_degree": +1,
    "clique_number": +1, "triangle_number": +1,
    "first_zagreb_index": +1, "second_zagreb_index": +1,
    "harmonic_index": +0.5,
    "largest_eigenvalue": +1,
    "second_smallest_laplace_eigenvalue": +1,
    "matching_number": +0.5, "vertex_cover_number": +0.5,
    "diameter": -1, "radius": -1,
    "proximity": +1, "remoteness": +1,
    "largest_distance_eigenvalue": -1,
    "independence_number": -1,
    "domination_number": -1, "total_domination_number": -1,
    "independent_domination_number": -1,
    "randic_index": -0.3,
}

# +1 : invariant grows roughly linearly with n. 0 : insensitive / bounded.
SIZE_BIAS = {
    "size": +1, "m": +1, "order": +1, "n": +1,
    "diameter": +1, "radius": +1, "remoteness": -0.3, "proximity": -0.3,
    "vertex_cover_number": +1, "matching_number": +1,
    "domination_number": +1, "total_domination_number": +1,
    "independent_domination_number": +1, "independence_number": +1,
    "clique_number": +0.3, "triangle_number": +0.5,
    "first_zagreb_index": +1, "second_zagreb_index": +1,
    "largest_eigenvalue": +0.3, "largest_distance_eigenvalue": +0.5,
    "second_smallest_laplace_eigenvalue": 0,
    "density": -0.5,
    "average_degree": 0, "minimum_degree": 0, "maximum_degree": +0.3,
    "randic_index": +0.5, "harmonic_index": +0.5,
}


def conjecture_directions(conjecture, x_val):
    """Return (dir_x, dir_y) in {-1, 0, +1}: sign of the change we want."""
    dir_y = +1 if conjecture.sign == "<=" else -1
    h = 1e-3
    try:
        slope = (conjecture.polynomial(x_val + h) - conjecture.polynomial(x_val - h)) / (2 * h)
    except Exception:
        slope = 0.0
    if conjecture.sign == "<=":
        dir_x = -1 if slope > 1e-9 else (+1 if slope < -1e-9 else 0)
    else:
        dir_x = +1 if slope > 1e-9 else (-1 if slope < -1e-9 else 0)
    return dir_x, dir_y


def heuristic_score(G, invariants_dict, conjecture):
    v = base_violation(invariants_dict, conjecture)
    if v > 1e-9:
        return 1e6 + v

    n = invariants_dict["n"]
    m = invariants_dict["m"]
    if n <= 1:
        return v - 100

    x_name = conjecture.x_invariant
    y_name = conjecture.y_invariant
    x_val = invariants_dict[x_name]

    dir_x, dir_y = conjecture_directions(conjecture, x_val)

    density = 2 * m / (n * (n - 1)) if n > 1 else 0.0

    score = v + 0.0005 * n

    # Direction-aware density push
    dens_target = dir_x * DENSITY_BIAS.get(x_name, 0.0) + dir_y * DENSITY_BIAS.get(y_name, 0.0)
    if dens_target > 0:
        score += 0.6 * (density - 0.5)
        if density > 0.85: score += 1.0
        if density > 0.95: score += 1.5
    elif dens_target < 0:
        score += 0.6 * (0.5 - density)
        if density < 0.15: score += 1.0
        if density < 0.05: score += 1.5
    else:
        if density < 0.05 or density > 0.95:
            score -= 0.2

    # Direction-aware size push
    size_target = dir_x * SIZE_BIAS.get(x_name, 0.0) + dir_y * SIZE_BIAS.get(y_name, 0.0)
    if size_target > 0:
        score += 0.03 * n
    elif size_target < 0:
        score -= 0.02 * n

    # Domain-specific tweaks kept from previous version
    dom = {"matching_number", "total_domination_number",
           "domination_number", "independent_domination_number"}
    if any(i in dom for i in (x_name, y_name)):
        leaves = sum(1 for _, d in G.degree() if d == 1)
        score += 0.05 * leaves
    if any(i in {"clique_number", "triangle_number"} for i in (x_name, y_name)):
        score += 0.002 * m

    return score
