import pandas as pd
import time
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
    
    total_start_time = time.time()  # Temps total début
    success_count = 0

    for i, c in enumerate(conjectures):
        print(f"\n====================")
        print(f"Conjecture {i+1}/{len(conjectures)} | ID = {c.conjecture_id}")
        print(f"====================")

        start_exec = time.time()  # Début chrono conjecture
        
        G, score = search(c, compute_invariant, time_limit=60)
        
        end_exec = time.time()  # Fin chrono conjecture
        exec_duration = end_exec - start_exec
        
        certificate = build_certificate(G, c)

        # Affichage résultat
        print(f"Score = {score}")
        print(f"Temps d'exécution = {exec_duration:.2f}s")

        if score > 0:
            print(">>> CONTRE-EXEMPLE TROUVÉ")
            success_count += 1
        else:
            print(">>> PAS DE CONTRE-EXEMPLE TROUVÉ")

        print("graph6 =", certificate["graph6"])

        # Stockage pour export
        results.append({
            "id": c.conjecture_id,
            "x": c.x_invariant,
            "y": c.y_invariant,
            "score": score,
            "nodes": certificate["nodes"],
            "edges": certificate["edges"],
            "x_value": certificate["x_value"],
            "y_value": certificate["y_value"],
            "graph6": certificate["graph6"],
            "exec_time_seconds": round(exec_duration, 2)
        })

    total_end_time = time.time()
    total_duration = total_end_time - total_start_time

    # --- BILAN FINAL ---
    print("\n" + "#"*40)
    print("RESUMÉ DES PERFORMANCES")
    print(f"Temps total mis : {total_duration:.2f} secondes")
    print(f"Score total : {success_count} / {len(conjectures)} conjectures réfutées")
    print("#"*40)

    # EXPORT EXCEL FINAL
    df = pd.DataFrame(results)
    df.to_excel("results_counterexamples.xlsx", index=False)
    print("\n>>> EXPORT TERMINÉ : results_counterexamples.xlsx")


if __name__ == "__main__":
    main()