def violation(G, conjecture, compute_invariant):

    x = compute_invariant(G, conjecture.x_invariant)
    y = compute_invariant(G, conjecture.y_invariant)

    f_x = 0

    for i, c in enumerate(conjecture.coefficients):
        f_x += c * (x ** (i + 1))

    f_x += conjecture.intercept

    if conjecture.sign == "<=":
        return y - f_x

    elif conjecture.sign == ">=":
        return f_x - y