import networkx as nx

def graph6(G):
    return nx.to_graph6_bytes(G).decode().strip()


def certificate(G, conjecture, compute_invariant):

    x = compute_invariant(G, conjecture.x_invariant)
    y = compute_invariant(G, conjecture.y_invariant)

    return {
        "n": G.number_of_nodes(),
        "m": G.number_of_edges(),
        "x": x,
        "y": y,
        "graph6": graph6(G)
    }