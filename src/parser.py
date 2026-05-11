import ast
import pandas as pd

from sympy import Rational

from src.conjecture import Conjecture


def parse_fraction(value):
    """
    Convertit une fraction texte en float.
    Exemple :
        '15/8' -> 1.875
    """

    return float(Rational(value))


def load_benchmark(path):
    df = pd.read_excel(path)

    conjectures = []

    for _, row in df.iterrows():

        coefficients_raw = ast.literal_eval(row["Coefficients"])

        coefficients = [
            parse_fraction(c)
            for c in coefficients_raw
        ]

        intercept = parse_fraction(str(row["Intercept"]))

        graph_classes = ast.literal_eval(row["Subgroup"])

        conjecture = Conjecture(
            conjecture_id=int(row["Conjecture ID"]),

            graph_classes=graph_classes,

            x_invariant=row["X"],
            y_invariant=row["Y"],

            sign=row["Sign"],

            coefficients=coefficients,
            intercept=intercept,
            degree=int(row["Degree"]),

            raw_expression=row["Conjecture"]
        )

        conjectures.append(conjecture)

    return conjectures