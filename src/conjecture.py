from dataclasses import dataclass


@dataclass
class Conjecture:
    conjecture_id: int

    graph_classes: list

    x_invariant: str
    y_invariant: str

    sign: str

    coefficients: list
    intercept: float
    degree: int

    raw_expression: str