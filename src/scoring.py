def base_violation(G, conjecture, compute_invariant):
    x = compute_invariant(G, conjecture.x_invariant)
    y = compute_invariant(G, conjecture.y_invariant)
    coefs = conjecture.coefficients
    deg = conjecture.degree
    poly = sum(coefs[i] * (x ** (i + 1)) for i in range(deg)) if deg >= 1 else 0
    poly += conjecture.intercept
    if conjecture.sign == '<=':
        return y - poly
    else:
        return poly - y


def heuristic_score(G, conjecture, compute_invariant):
    v = base_violation(G, conjecture, compute_invariant)
    if v > 0:
        return v + 10000

    n = G.number_of_nodes()
    m = G.number_of_edges()
    score = v

    # Spécial conjecture 1587 (total_domination_number vs matching_number)
    if conjecture.conjecture_id == 1587:
        matching = compute_invariant(G, 'matching_number')
        total_dom = compute_invariant(G, 'total_domination_number')
        # Bonus fort pour écart total_dom - matching (on veut matching petit)
        score += 2.0 * (total_dom - matching)
    else:
        if n > 1:
            density = 2 * m / (n * (n - 1))
            score += 0.01 * (1 - density)
        if 'tree' in conjecture.graph_classes:
            cycles = m - n + 1
            score -= 0.02 * cycles

    return score