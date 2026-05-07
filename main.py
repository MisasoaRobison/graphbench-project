import pandas as pd
from src.parser import load_benchmark
from src.invariants import compute_invariant
from src.graph6 import graph6
from src.scoring import violation
from src.search import search


def build_certificate(G, c):
    """Construit une preuve calculatoire propre"""

    return {
        "id": c.conjecture_id,
        "x_invariant": c.x_invariant,
        "y_invariant": c.y_invariant,
        "x_value": compute_invariant(G, c.x_invariant),
        "y_value": compute_invariant(G, c.y_invariant),
        "graph6": graph6(G),
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges()
    }


def main():

    conjectures = load_benchmark("benchmark/benchmark.xlsx")

    results = []

    # 👉 on prend les 10 premières conjectures
    for i, c in enumerate(conjectures[:10]):

        print(f"\n====================")
        print(f"Conjecture {i+1} | ID = {c.conjecture_id}")
        print(f"====================")

        G, score = search(c, compute_invariant, time_limit=60)

        certificate = build_certificate(G, c)

        # -----------------------------
        # affichage résultat
        # -----------------------------
        print("Score =", score)

        if score > 0:
            print(">>> CONTRE-EXEMPLE TROUVÉ (CONJECTURE FAUSSE)")
        else:
            print(">>> PAS DE CONTRE-EXEMPLE TROUVÉ DANS LE TEMPS")

        print("graph6 =", certificate["graph6"])

        # -----------------------------
        # stockage pour export Excel
        # -----------------------------
        results.append({
            "id": c.conjecture_id,
            "x": c.x_invariant,
            "y": c.y_invariant,
            "score": score,
            "nodes": certificate["nodes"],
            "edges": certificate["edges"],
            "x_value": certificate["x_value"],
            "y_value": certificate["y_value"],
            "graph6": certificate["graph6"]
        })

    # -----------------------------
    # EXPORT EXCEL FINAL
    # -----------------------------
    df = pd.DataFrame(results)
    df.to_excel("results_counterexamples.xlsx", index=False)

    print("\n\n>>> EXPORT TERMINÉ : results_counterexamples.xlsx")


if __name__ == "__main__":
    main()