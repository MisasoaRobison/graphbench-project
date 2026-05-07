import time
import random
import networkx as nx
from src.graph_generation import generate_graph
from src.scoring import base_violation, heuristic_score
from src.repair import repair_class

def mutate(G):
    H = G.copy()
    nodes = list(H.nodes())
    if len(nodes) < 2:
        return generate_graph(None)   # fallback
    action = random.choices(
        ["add_edge", "remove_edge", "rewire", "clique", "star"],
        weights=[2, 2, 3, 2, 2],
        k=1
    )[0]
    if action == "add_edge":
        u, v = random.sample(nodes, 2)
        H.add_edge(u, v)
    elif action == "remove_edge" and H.number_of_edges() > 0:
        u, v = random.choice(list(H.edges()))
        H.remove_edge(u, v)
    elif action == "rewire" and H.number_of_edges() > 0:
        u, v = random.choice(list(H.edges()))
        H.remove_edge(u, v)
        x, y = random.sample(nodes, 2)
        H.add_edge(x, y)
    elif action == "clique":
        subset = random.sample(nodes, min(len(nodes), 5))
        for i in subset:
            for j in subset:
                if i != j:
                    H.add_edge(i, j)
    elif action == "star":
        center = random.choice(nodes)
        for v in nodes:
            if v != center:
                H.add_edge(center, v)
    return H

def search(conjecture, compute_invariant, time_limit=60):
    start = time.time()
    G = generate_graph(conjecture)
    G = repair_class(G, conjecture.graph_classes)
    best_G = G
    best_score = heuristic_score(G, conjecture, compute_invariant)
    best_viol = base_violation(G, conjecture, compute_invariant)

    stagnation = 0
    while time.time() - start < time_limit:
        H = mutate(best_G)
        H = repair_class(H, conjecture.graph_classes)
        sc = heuristic_score(H, conjecture, compute_invariant)
        if sc > best_score:
            best_score = sc
            best_G = H
            best_viol = base_violation(H, conjecture, compute_invariant)
            stagnation = 0
            if best_viol > 0:
                return H, best_viol
        else:
            stagnation += 1
        if stagnation > 30:
            # redémarrage
            G2 = generate_graph(conjecture)
            G2 = repair_class(G2, conjecture.graph_classes)
            best_score = heuristic_score(G2, conjecture, compute_invariant)
            best_viol = base_violation(G2, conjecture, compute_invariant)
            best_G = G2
            stagnation = 0
    return best_G, best_viol