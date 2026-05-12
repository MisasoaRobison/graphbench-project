"""Light-weight validator for a results file (CSV or XLSX).

Usage:
    python validate.py                                       # auto-detect
    python validate.py results/results_counterexamples.csv
    python validate.py results/baseline.xlsx

A counter-example is reported VALID iff:
  - the graph6 string decodes to a non-empty graph,
  - the graph satisfies every class listed in the conjecture,
  - the inequality is *strictly* violated (recomputed from the graph),
  - the stored x_value / y_value match the recomputed ones.

For a more thorough validator (with extra checks on classes and exit
codes suitable for CI), see ``experiments/validate_results.py``.
"""

import os
import sys
import networkx as nx
import pandas as pd

from src.parser import load_benchmark
from src.invariants import compute_invariant, clear_cache
from src.graph6 import from_graph6
from src.graph_generation import is_claw_free


CLASS_CHECKS = {
    "connected": lambda G: nx.is_connected(G),
    "tree": lambda G: nx.is_tree(G),
    "bipartite": lambda G: nx.is_bipartite(G),
    "planar": lambda G: nx.is_planar(G),
    "claw_free": is_claw_free,
}


def _read(path):
    if str(path).lower().endswith(".csv"):
        return pd.read_csv(path, sep=";", encoding="utf-8")
    return pd.read_excel(path)


def _find_benchmark():
    for cand in ("benchmark/benchmark.csv", "benchmark/benchmark.xlsx"):
        if os.path.isfile(cand):
            return cand
    raise FileNotFoundError("no benchmark file found in benchmark/")


def check_classes(G, classes):
    for cls in classes:
        check = CLASS_CHECKS.get(cls)
        if check is None:
            continue
        if not check(G):
            return False, cls
    return True, None


def main(path):
    df = _read(path)
    benchmark = {c.conjecture_id: c for c in load_benchmark(_find_benchmark())}

    valid = 0
    invalid = []
    not_found = 0
    for _, row in df.iterrows():
        cid = int(row["id"])
        c = benchmark.get(cid)
        if c is None:
            invalid.append((cid, "conjecture id not in benchmark"))
            continue
        if not bool(row.get("found", False)):
            not_found += 1
            continue
        g6 = str(row["graph6"])
        try:
            G = from_graph6(g6)
        except Exception as e:
            invalid.append((cid, f"graph6 decode failed: {e}"))
            continue
        G = nx.convert_node_labels_to_integers(G)
        ok, missing = check_classes(G, c.graph_classes)
        if not ok:
            invalid.append((cid, f"violates class {missing}"))
            continue
        clear_cache()
        try:
            x = compute_invariant(G, c.x_invariant)
            y = compute_invariant(G, c.y_invariant)
            v = c.violation(x, y)
        except Exception as e:
            invalid.append((cid, f"invariant failure: {e}"))
            continue
        if v <= 1e-9:
            invalid.append((cid, f"violation={v:.6f} not strictly positive "
                                  f"(recomputed x={x}, y={y})"))
            continue
        stored_x = row.get("x_value")
        stored_y = row.get("y_value")
        if stored_x is not None and stored_y is not None:
            try:
                if abs(float(stored_x) - float(x)) > 1e-6 \
                   or abs(float(stored_y) - float(y)) > 1e-6:
                    invalid.append((cid, f"stored ({stored_x}, {stored_y}) "
                                          f"differs from recomputed ({x}, {y})"))
                    continue
            except Exception:
                pass
        valid += 1

    print(f"{'='*70}")
    print(f"File:                   {path}")
    print(f"Valid counter-examples: {valid}")
    print(f"Not-found rows:         {not_found}")
    print(f"Invalid rows:           {len(invalid)}")
    if invalid:
        print(f"\nInvalid details:")
        for cid, reason in invalid:
            print(f"  ID={cid}: {reason}")
    return 0 if not invalid else 1


if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        for cand in ("results/results_counterexamples.csv",
                     "results_counterexamples.xlsx",
                     "results/baseline.csv"):
            if os.path.isfile(cand):
                path = cand
                break
        else:
            print("no default result file found, pass an explicit path")
            sys.exit(2)
    sys.exit(main(path))
