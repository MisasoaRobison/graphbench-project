import random
import networkx as nx


def _ensure_connected(G):
    if G.number_of_nodes() == 0: return G
    if nx.is_connected(G): return G
    H = G.copy(); comps = [list(c) for c in nx.connected_components(H)]; main = comps[0]
    for c in comps[1:]:
        H.add_edge(random.choice(main), random.choice(c)); main += c
    return H


def _ensure_tree(G):
    if G.number_of_nodes() == 0: return G
    H = _ensure_connected(G)
    if H.number_of_edges() == H.number_of_nodes() - 1:
        return H
    return nx.minimum_spanning_tree(H)


def _ensure_bipartite(G):
    if nx.is_bipartite(G): return G
    H = G.copy()
    while not nx.is_bipartite(H):
        try:
            cycle = nx.find_cycle(H)
        except nx.NetworkXNoCycle:
            break
        H.remove_edge(cycle[0][0], cycle[0][1])
    return _ensure_connected(H)


def _ensure_planar(G):
    if nx.is_planar(G): return G
    H = G.copy(); edges = list(H.edges()); random.shuffle(edges)
    while not nx.is_planar(H) and edges:
        e = edges.pop()
        if H.has_edge(*e):
            H.remove_edge(*e)
    return _ensure_connected(H)


def _claws(G, v):
    nbrs = list(G.neighbors(v))
    if len(nbrs) < 3: return
    for i in range(len(nbrs)):
        for j in range(i+1, len(nbrs)):
            if G.has_edge(nbrs[i], nbrs[j]): continue
            for k in range(j+1, len(nbrs)):
                if not G.has_edge(nbrs[i], nbrs[k]) and not G.has_edge(nbrs[j], nbrs[k]):
                    yield (nbrs[i], nbrs[j], nbrs[k])


def _ensure_claw_free(G):
    H = G.copy()
    for _ in range(200):
        broken = False
        for v in list(H.nodes()):
            for triple in _claws(H, v):
                pair = random.sample(list(triple), 2)
                H.add_edge(pair[0], pair[1]); broken = True; break
            if broken: break
        if not broken: break
    return _ensure_connected(H)


def repair_class(G, graph_classes):
    classes = set(graph_classes or []); H = G
    if "tree" in classes:
        return _ensure_tree(H)
    if "bipartite" in classes:
        H = _ensure_bipartite(H)
    if "planar" in classes:
        H = _ensure_planar(H)
    if "claw_free" in classes:
        H = _ensure_claw_free(H)
    if "connected" in classes:
        H = _ensure_connected(H)
    return H
