import time
import random

from src.graph_generation import generate_graph
from src.scoring import violation


def mutate(G):
    H = G.copy()
    nodes = list(H.nodes())

    if len(nodes) < 2:
        return generate_graph()

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

    G = generate_graph()
    best_G = G
    best_score = violation(G, conjecture, compute_invariant)

    stagnation = 0

    while time.time() - start < time_limit:

        H = mutate(best_G)   # 🔥 IMPORTANT : centre toujours best_G
        score = violation(H, conjecture, compute_invariant)

        if score > best_score:
            best_score = score
            best_G = H
            stagnation = 0

        else:
            stagnation += 1

        if score > 0:
            return H, score

        if stagnation > 30:
            G = generate_graph()
            best_G = G
            best_score = violation(G, conjecture, compute_invariant)
            stagnation = 0

    return best_G, best_score