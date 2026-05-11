import argparse
import os
import sys
import time
import pandas as pd

from src.parser import load_benchmark
from src.invariants import compute_invariant, clear_cache
from src.graph6 import graph6
from src.search import search


def build_certificate(G, c):
    return {
        "id": c.conjecture_id,
        "x_invariant": c.x_invariant,
        "y_invariant": c.y_invariant,
        "x_value": compute_invariant(G, c.x_invariant),
        "y_value": compute_invariant(G, c.y_invariant),
        "graph6": graph6(G),
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
    }


def log(m):
    print(m, flush=True)


def main():
    log("=== START ===")
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", default="benchmark/benchmark.csv")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--time", type=float, default=60.0)
    parser.add_argument("--output", default="results/results_counterexamples.csv")
    parser.add_argument("--ids", type=str, default=None)
    args = parser.parse_args()

    log("Loading benchmark from " + args.benchmark + " ...")
    conjectures = load_benchmark(args.benchmark)
    log("Loaded " + str(len(conjectures)) + " conjectures.")

    if args.ids:
        wanted = {int(x) for x in args.ids.split(",")}
        conjectures = [c for c in conjectures if c.conjecture_id in wanted]
        log("Filtered to " + str(len(conjectures)) + " by ID.")
    elif args.limit is not None:
        conjectures = conjectures[: args.limit]
        log("Limited to first " + str(len(conjectures)) + ".")

    if not conjectures:
        log("No conjectures to run."); return

    results = []; total_cost = 0.0; refuted = 0

    for i, c in enumerate(conjectures, 1):
        log("\n[" + str(i) + "/" + str(len(conjectures)) + "] ID=" + str(c.conjecture_id)
            + "  " + c.y_invariant + " " + c.sign + " f(" + c.x_invariant + ")"
            + "  classes=" + str(c.graph_classes))
        clear_cache()
        t0 = time.time()
        G, viol, info = search(c, time_limit=args.time)
        elapsed = time.time() - t0

        if G is not None and viol > 1e-9:
            cert = build_certificate(G, c); cost = elapsed; refuted += 1
            log("  -> COUNTER-EXAMPLE  v=" + str(round(viol, 4))
                + "  n=" + str(cert["nodes"])
                + "  " + c.x_invariant + "=" + str(cert["x_value"])
                + "  " + c.y_invariant + "=" + str(cert["y_value"])
                + "  phase=" + info["phase"]
                + "  evals=" + str(info["n_evaluated"])
                + "  t=" + str(round(elapsed, 2)) + "s")
            results.append({
                "id": c.conjecture_id, "found": True,
                "x_invariant": c.x_invariant, "y_invariant": c.y_invariant,
                "x_value": cert["x_value"], "y_value": cert["y_value"],
                "violation": viol,
                "nodes": cert["nodes"], "edges": cert["edges"],
                "graph6": cert["graph6"], "phase": info["phase"],
                "evaluations": info["n_evaluated"], "elapsed_s": elapsed,
            })
        else:
            cost = 120.0
            log("  -> NO COUNTER-EXAMPLE   best v=" + str(round(viol, 4) if viol != float("-inf") else viol)
                + "  evals=" + str(info["n_evaluated"])
                + "  t=" + str(round(elapsed, 2)) + "s")
            cert = build_certificate(G, c) if G is not None else {
                "nodes": 0, "edges": 0, "graph6": "",
                "x_value": None, "y_value": None}
            results.append({
                "id": c.conjecture_id, "found": False,
                "x_invariant": c.x_invariant, "y_invariant": c.y_invariant,
                "x_value": cert.get("x_value"), "y_value": cert.get("y_value"),
                "violation": viol,
                "nodes": cert.get("nodes"), "edges": cert.get("edges"),
                "graph6": cert.get("graph6"), "phase": info["phase"],
                "evaluations": info["n_evaluated"], "elapsed_s": elapsed,
            })
        total_cost += cost

    out_dir = os.path.dirname(args.output)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    df_out = pd.DataFrame(results)
    if str(args.output).lower().endswith(".csv"):
        df_out.to_csv(args.output, index=False, sep=";", encoding="utf-8")
    else:
        df_out.to_excel(args.output, index=False)
    log("\n" + "=" * 70)
    log("Refuted " + str(refuted) + "/" + str(len(conjectures)) + " conjectures.")
    log("Total cost: " + str(round(total_cost, 2)))
    log("Results -> " + args.output)


try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass
main()
