import networkx as nx
import random

def generate_graph(n=None, classes=None):
    if n is None: n = random.randint(6, 12)
    
    # On gère les arbres spécifiquement
    if classes and "tree" in str(classes):
        if hasattr(nx, 'random_labeled_tree'):
            return nx.random_labeled_tree(n)
        return nx.random_tree(n)

    # Sinon, Erdős-Rényi classique
    p = random.choice([0.2, 0.4, 0.6])
    G = nx.erdos_renyi_graph(n, p)

    # Réparation systématique de la connexité
    if not nx.is_connected(G):
        components = list(nx.connected_components(G))
        for i in range(len(components)-1):
            u = random.choice(list(components[i]))
            v = random.choice(list(components[i+1]))
            G.add_edge(u, v)
    return G