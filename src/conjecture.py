from dataclasses import dataclass
from typing import List


@dataclass
class Conjecture:
    conjecture_id: int
    graph_classes: list
    x_invariant: str
    y_invariant: str
    sign: str
    coefficients: List[float]
    intercept: float
    degree: int
    raw_expression: str

    def polynomial(self, x):
        result = self.intercept
        for i, c in enumerate(self.coefficients):
            result += c * (x ** (i + 1))
        return result

    def violation(self, *args):
        """Compute violation as a positive number when the conjecture is violated.

        Two call shapes are supported:
            violation(x, y)
            violation(invariants_dict)   # looks up x_invariant and y_invariant
        """
        if len(args) == 1 and isinstance(args[0], dict):
            inv = args[0]
            x = inv[self.x_invariant]
            y = inv[self.y_invariant]
        elif len(args) == 2:
            x, y = args
        else:
            raise TypeError("violation expects (x, y) or (invariants_dict)")
        poly = self.polynomial(x)
        if self.sign == "<=":
            return y - poly
        else:
            return poly - y
