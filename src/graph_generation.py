import networkx as nx
import random

def generate_special_1587():
    """Graphe peigne amélioré pour la conjecture 1587"""
    k = random.randint(5, 15)  # nombre de dents, augmenté
    G = nx.Graph()
    # Chaîne principale
    for i in range(2*k - 1):
        G.add_edge(i, i+1)
    # Ajout des dents (feuilles sur sommets pairs)
    for i in range(0, 2*k, 2):
        leaf = 2*k + i//2
        G.add_edge(i, leaf)
        # Optionnel : ajouter une deuxième feuille pour plus d'écart
        if random.random() < 0.3:
            leaf2 = 2*k + k + i//2
            G.add_node(leaf2)
            G.add_edge(leaf, leaf2)
    return G

def generate_connected(min_n=5, max_n=15):
    n = random.randint(min_n, max_n)
    p = random.uniform(0.1, 0.5)
    G = nx.erdos_renyi_graph(n, p)
    if not nx.is_connected(G):
        comps = list(nx.connected_components(G))
        for i in range(len(comps) - 1):
            u = random.choice(list(comps[i]))
            v = random.choice(list(comps[i+1]))
            G.add_edge(u, v)
    return G

def generate_tree(min_n=5, max_n=30):
    n = random.randint(min_n, max_n)
    return nx.random_tree(n)

def generate_bipartite(min_n=5, max_n=30):
    n1 = random.randint(2, max_n // 2)
    n2 = random.randint(2, max_n - n1)
    p = random.uniform(0.2, 0.8)
    G = nx.bipartite.random_graph(n1, n2, p)
    if not nx.is_connected(G):
        G = nx.star_graph(min(n1, n2))
        G = nx.convert_node_labels_to_integers(G)
    return G

def generate_planar(min_n=5, max_n=20):
    n = random.randint(min_n, max_n)
    G = nx.random_geometric_graph(n, radius=0.4)
    if not nx.is_planar(G):
        r = int(n ** 0.5)
        G = nx.grid_2d_graph(r, r + 1 if r * (r + 1) >= n else r)
        G = nx.convert_node_labels_to_integers(G)
    return G

def generate_claw_free(min_n=5, max_n=20):
    n = random.randint(min_n, max_n)
    if random.random() < 0.5:
        return nx.path_graph(n)
    else:
        return nx.cycle_graph(n)

def generate_graph(conjecture):
    # Spécial pour la conjecture 1587
    if conjecture.conjecture_id == 1587:
        return generate_special_1587()

    classes = conjecture.graph_classes
    if 'tree' in classes:
        return generate_tree()
    if 'bipartite' in classes:
        return generate_bipartite()
    if 'planar' in classes:
        return generate_planar()
    if 'claw_free' in classes:
        return generate_claw_free()
    return generate_connected()