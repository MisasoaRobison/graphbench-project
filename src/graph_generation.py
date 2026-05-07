import networkx as nx
import random

def generate_graph(n=10):

    p = random.choice([0.1, 0.3, 0.7])

    G = nx.erdos_renyi_graph(n, p)

    if not nx.is_connected(G):
        components = list(nx.connected_components(G))
        for i in range(len(components)-1):
            u = list(components[i])[0]
            v = list(components[i+1])[0]
            G.add_edge(u, v)

    return G