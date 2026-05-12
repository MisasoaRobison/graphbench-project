"""Compare two result spreadsheets head-to-head.

Usage:
    python experiments/compare.py results/baseline_static.xlsx results/evolved.xlsx

Prints, for each spreadsheet:
  - number of conjectures refuted
  - total cost (sum of t_i, 120 when not refuted)
  - average refutation time

Then shows the per-ID delta: which IDs one heuristic refutes that the other
doesn't, and where the time differential is largest.
"""

import sys
import pandas as pd


def _read(path):
    if str(path).lower().endswith(".csv"):
        return pd.read_csv(path, sep=";", encoding="utf-8")
    return pd.read_excel(path)


def summary(path):
    df = _read(path)
    refuted = df[df["found"] == True]
    n_refuted = len(refuted)
    n_total = len(df)
    total_cost = refuted["elapsed_s"].sum() + (n_total - n_refuted) * 120.0
    avg_t = refuted["elapsed_s"].mean() if n_refuted else float("nan")
    return n_refuted, n_total, total_cost, avg_t, refuted


def compare(path_a, path_b):
    a_n, a_t, a_cost, a_avg, a_ref = summary(path_a)
    b_n, b_t, b_cost, b_avg, b_ref = summary(path_b)
    print(f"{'':24s} {'A':>16s} {'B':>16s}")
    print(f"{'file':24s} {path_a:>16s} {path_b:>16s}")
    print(f"{'refuted':24s} {a_n:>12d}/{a_t:<3d} {b_n:>12d}/{b_t:<3d}")
    print(f"{'total cost (sec)':24s} {a_cost:>16.2f} {b_cost:>16.2f}")
    print(f"{'avg t per refute':24s} {a_avg:>16.2f} {b_avg:>16.2f}")
    print()

    a_ids = set(a_ref["id"])
    b_ids = set(b_ref["id"])
    only_a = sorted(a_ids - b_ids)
    only_b = sorted(b_ids - a_ids)
    print(f"Only in A ({len(only_a)} IDs): {only_a}")
    print(f"Only in B ({len(only_b)} IDs): {only_b}")

    common = a_ids & b_ids
    if common:
        a_times = a_ref.set_index("id")["elapsed_s"]
        b_times = b_ref.set_index("id")["elapsed_s"]
        deltas = (b_times - a_times).reindex(sorted(common)).dropna()
        print(f"\nTime delta (B - A) on the {len(common)} common refutations:")
        print(f"  mean: {deltas.mean():+.2f}s")
        print(f"  median: {deltas.median():+.2f}s")
        worst = deltas.abs().sort_values(ascending=False).head(5)
        for cid, _ in worst.items():
            print(f"  ID={cid}: A={a_times[cid]:.2f}s  B={b_times[cid]:.2f}s  "
                  f"delta={deltas[cid]:+.2f}s")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python experiments/compare.py FILE_A FILE_B")
        sys.exit(1)
    compare(sys.argv[1], sys.argv[2])
