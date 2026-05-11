import time
import random
import networkx as nx
from src.graph_generation import generate_graph
from src.scoring import violation

def mutate(G, classes=None):
    H = G.copy()
    nodes = list(H.nodes())

    if len(nodes) < 3:
        return generate_graph(classes=classes)

    # Ajout de 'subdivide' pour construire des structures plus complexes
    action = random.choices(
        ["add_edge", "remove_edge", "rewire", "clique", "star", "subdivide"],
        weights=[2, 2, 3, 2, 2, 3],
        k=1
    )[0]

    try:
        if action == "add_edge":
            u, v = random.sample(nodes, 2)
            H.add_edge(u, v)
        elif action == "remove_edge" and H.number_of_edges() > 1:
            e = random.choice(list(H.edges()))
            H.remove_edge(*e)
        elif action == "rewire" and H.number_of_edges() > 0:
            e = random.choice(list(H.edges()))
            H.remove_edge(*e)
            u, v = random.sample(nodes, 2)
            H.add_edge(u, v)
        elif action == "clique":
            subset = random.sample(nodes, min(len(nodes), 4))
            for i in subset:
                for j in subset:
                    if i != j: H.add_edge(i, j)
        elif action == "star":
            center = random.choice(nodes)
            for v in nodes:
                if v != center: H.add_edge(center, v)
        elif action == "subdivide" and H.number_of_edges() > 0:
            u, v = random.choice(list(H.edges()))
            H.remove_edge(u, v)
            new_node = max(nodes) + 1
            H.add_edge(u, new_node)
            H.add_edge(new_node, v)
    except:
        pass

    # --- ÉTAPE DE RÉPARATION (Crucial pour le prof) ---
    if not nx.is_connected(H):
        components = list(nx.connected_components(H))
        for i in range(len(components)-1):
            u, v = random.choice(list(components[i])), random.choice(list(components[i+1]))
            H.add_edge(u, v)
            
    # Si c'est un arbre, on retire les cycles créés par 'add_edge' ou 'clique'
    if classes and "tree" in str(classes):
        while True:
            try:
                cycle = nx.find_cycle(H)
                H.remove_edge(*cycle[0])
            except nx.NetworkXNoCycle:
                break

    return H

def search(conjecture, compute_invariant, time_limit=60):
    start = time.time()
    # On passe les classes au générateur
    G = generate_graph(classes=conjecture.graph_classes)
    best_G = G
    best_score = violation(G, conjecture, compute_invariant)
    stagnation = 0

    while time.time() - start < time_limit:
        # On mute à partir du meilleur pour "grimper" vers le contre-exemple
        H = mutate(best_G, classes=conjecture.graph_classes)
        score = violation(H, conjecture, compute_invariant)

        if score > best_score:
            best_score = score
            best_G = H
            stagnation = 0
        else:
            stagnation += 1

        if score > 0.0001: # Trouvé !
            return H, score

        # Redémarrage si on est bloqué dans un "trou" (minimum local)
        if stagnation > 50:
            G = generate_graph(n=random.randint(6, 18), classes=conjecture.graph_classes)
            best_G = G
            best_score = violation(G, conjecture, compute_invariant)
            stagnation = 0

    return best_G, best_score