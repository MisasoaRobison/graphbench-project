import pandas as pd
from src.parser import load_benchmark
from src.invariants import compute_invariant
from src.graph6 import graph6
from src.scoring import base_violation
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

    # On prend les 10 premières conjectures
    for i, c in enumerate(conjectures[:10]):
        print(f"\n====================")
        print(f"Conjecture {i+1} | ID = {c.conjecture_id}")
        print(f"====================")

        # Temps plus long pour la conjecture difficile 1587
        if c.conjecture_id == 1587:
            time_limit = 120
            print("  (Temps alloué : 120 secondes pour cette conjecture difficile)")
        else:
            time_limit = 60

        G, score = search(c, compute_invariant, time_limit=time_limit)

        certificate = build_certificate(G, c)

        print(f"Score = {score:.6f}")

        if score > 0:
            print(">>> CONTRE-EXEMPLE TROUVÉ (CONJECTURE FAUSSE)")
        else:
            print(">>> PAS DE CONTRE-EXEMPLE TROUVÉ DANS LE TEMPS")

        print(f"graph6 = {certificate['graph6']}")
        print(f"n = {certificate['nodes']}, m = {certificate['edges']}")
        print(f"{c.x_invariant} = {certificate['x_value']}, {c.y_invariant} = {certificate['y_value']}")

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

    # Export Excel final
    df = pd.DataFrame(results)
    df.to_excel("results_counterexamples.xlsx", index=False)

    # Affichage du résumé
    print("\n\n" + "="*60)
    print("RÉSUMÉ DES RÉSULTATS")
    print("="*60)
    for r in results:
        status = "✓" if r["score"] > 0 else "✗"
        print(f"{status} ID {r['id']:4d} : score = {r['score']:8.4f}   (n={r['nodes']}, {r['x']}={r['x_value']}, {r['y']}={r['y_value']})")
    print("="*60)
    print(f"\n>>> EXPORT TERMINÉ : results_counterexamples.xlsx")


if __name__ == "__main__":
    main()