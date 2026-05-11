def heuristic_score(G, invariants, conjecture):
    # The simplest possible score: just the raw violation.
    return conjecture.violation(invariants)
