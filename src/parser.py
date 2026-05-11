import ast
import pandas as pd
from sympy import Rational
from src.conjecture import Conjecture


def parse_fraction(value):
    return float(Rational(str(value)))


def load_benchmark(path):
    if str(path).lower().endswith(".csv"):
        df = pd.read_csv(path, sep=";", encoding="cp1252")
    else:
        df = pd.read_excel(path)
    conjectures = []
    for _, row in df.iterrows():
        coefficients_raw = ast.literal_eval(str(row["Coefficients"]))
        coefficients = [parse_fraction(c) for c in coefficients_raw]
        intercept = parse_fraction(str(row["Intercept"]))
        graph_classes = ast.literal_eval(str(row["Subgroup"]))
        conjectures.append(Conjecture(
            conjecture_id=int(row["Conjecture ID"]),
            graph_classes=graph_classes,
            x_invariant=row["X"],
            y_invariant=row["Y"],
            sign=row["Sign"],
            coefficients=coefficients,
            intercept=intercept,
            degree=int(row["Degree"]),
            raw_expression=str(row["Conjecture"]),
        ))
    return conjectures
