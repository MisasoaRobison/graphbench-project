import networkx as nx


def relabel(G):
    return nx.convert_node_labels_to_integers(G, first_label=0, ordering="default")


def graph6(G):
    H = relabel(G)
    return nx.to_graph6_bytes(H, header=False).decode().strip()


def from_graph6(s):
    return nx.from_graph6_bytes(s.encode())
