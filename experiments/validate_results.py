"""Independent validator for `results_counterexamples.csv`.

Re-checks every claimed counter-example against the four rules of §11:
    1. the graph belongs to the imposed class,
    2. the listed invariants are correctly computed,
    3. the inequality is strictly violated,
    4. the graph is supplied at the graph6 format.

Run:
    python -m experiments.validate_results \\
        --results results/results_counterexamples.csv \\
        --benchmark benchmark/benchmark.csv
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import pandas as pd
import networkx as nx

from src.parser import load_benchmark
from src.invariants import compute_invariant, clear_cache
from src.graph_generation import is_claw_free


CLASS_CHECKS = {
    "connected": lambda G: G.number_of_nodes() >= 1 and nx.is_connected(G),
    "tree": lambda G: G.number_of_nodes() >= 1 and nx.is_tree(G),
    "bipartite": lambda G: nx.is_bipartite(G),
    "planar": lambda G: nx.is_planar(G),
    "claw_free": is_claw_free,
}


def decode_graph6(s: str) -> nx.Graph:
    """Decode a graph6 string and renumber nodes to 0..n-1."""
    G = nx.from_graph6_bytes(s.encode("ascii"))
    return nx.convert_node_labels_to_integers(G)


def parse_classes(raw) -> list[str]:
    """The benchmark stores classes as a Python literal list of strings."""
    import ast
    return ast.literal_eval(str(raw))


def approx_eq(a, b, rtol=1e-6, atol=1e-6):
    if a == b:
        return True
    try:
        return abs(float(a) - float(b)) <= atol + rtol * max(abs(float(a)), abs(float(b)))
    except (TypeError, ValueError):
        return False


def validate_row(row, conjecture):
    """Validate one row. Returns (ok: bool, reasons: list[str], info: dict)."""
    reasons: list[str] = []
    info: dict = {}

    # Rule 4 — graph6 format.
    g6 = row.get("graph6", "")
    if not isinstance(g6, str) or not g6:
        reasons.append("missing graph6 encoding")
        return False, reasons, info
    try:
        G = decode_graph6(g6)
    except Exception as e:
        reasons.append(f"graph6 decode failed: {e!r}")
        return False, reasons, info

    info["decoded_n"] = G.number_of_nodes()
    info["decoded_m"] = G.number_of_edges()

    # Rule 1 — class membership.
    classes = conjecture.graph_classes
    for cls in classes:
        check = CLASS_CHECKS.get(cls)
        if check is None:
            reasons.append(f"unknown class {cls!r}")
        elif not check(G):
            reasons.append(f"class {cls!r} not satisfied by the decoded graph")

    # Rule 2 — invariant values match.
    clear_cache()
    x_actual = compute_invariant(G, conjecture.x_invariant)
    y_actual = compute_invariant(G, conjecture.y_invariant)
    info["x_recomputed"] = x_actual
    info["y_recomputed"] = y_actual

    if not approx_eq(x_actual, row.get("x_value")):
        reasons.append(
            f"x_value mismatch: stored={row.get('x_value')} recomputed={x_actual}")
    if not approx_eq(y_actual, row.get("y_value")):
        reasons.append(
            f"y_value mismatch: stored={row.get('y_value')} recomputed={y_actual}")

    # Rule 3 — strict violation under recomputed invariants.
    violation = conjecture.violation(x_actual, y_actual)
    info["violation_recomputed"] = violation
    if violation <= 1e-9:
        reasons.append(
            f"inequality not strictly violated (violation={violation:.6g})")

    return len(reasons) == 0, reasons, info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/results_counterexamples.csv")
    ap.add_argument("--benchmark", default="benchmark/benchmark.csv")
    ap.add_argument("--show-info", action="store_true",
                    help="print per-row recomputed invariants")
    args = ap.parse_args()

    results_path = Path(args.results)
    if not results_path.exists():
        print(f"results file not found: {results_path}", file=sys.stderr)
        sys.exit(2)

    # Load conjectures keyed by id.
    conjectures = {c.conjecture_id: c for c in load_benchmark(args.benchmark)}

    # Load results (sep depends on extension).
    if str(args.results).lower().endswith(".csv"):
        df = pd.read_csv(args.results, sep=";")
    else:
        df = pd.read_excel(args.results)

    total = len(df)
    claimed = int(df["found"].sum()) if "found" in df.columns else total
    valid = 0
    failures = []

    for _, row in df.iterrows():
        if "found" in df.columns and not bool(row["found"]):
            continue
        cid = int(row["id"])
        c = conjectures.get(cid)
        if c is None:
            failures.append((cid, ["unknown conjecture id in benchmark"]))
            continue
        ok, reasons, info = validate_row(row, c)
        if ok:
            valid += 1
            if args.show_info:
                print(f"  OK  id={cid}  n={info['decoded_n']} m={info['decoded_m']} "
                      f"x={info['x_recomputed']} y={info['y_recomputed']} "
                      f"v={info['violation_recomputed']:.6g}")
        else:
            failures.append((cid, reasons))

    print("=" * 70)
    print(f"results file : {results_path}")
    print(f"rows in file : {total}")
    print(f"claimed found: {claimed}")
    print(f"validated    : {valid} / {claimed}")
    print(f"failures     : {len(failures)}")

    for cid, reasons in failures:
        print(f"  [ID {cid}] {'; '.join(reasons)}")

    sys.exit(0 if not failures else 1)


if __name__ == "__main__":
    main()
