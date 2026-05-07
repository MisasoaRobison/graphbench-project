import networkx as nx
import random

def repair_class(G, classes):
    H = G.copy()
    if 'connected' in classes and not nx.is_connected(H):
        comps = list(nx.connected_components(H))
        for i in range(len(comps) - 1):
            u = random.choice(list(comps[i]))
            v = random.choice(list(comps[i + 1]))
            H.add_edge(u, v)
    if 'tree' in classes:
        while H.number_of_edges() >= H.number_of_nodes() and H.number_of_nodes() > 0:
            try:
                cycle = nx.find_cycle(H, orientation='ignore')
                if cycle:
                    H.remove_edge(cycle[0][0], cycle[0][1])
                else:
                    break
            except:
                break
    if 'bipartite' in classes and not nx.is_bipartite(H):
        # reconstruction d'un graphe biparti connexe
        n = H.number_of_nodes()
        left = set(random.sample(range(n), n // 2))
        right = set(range(n)) - left
        H = nx.Graph()
        H.add_nodes_from(left, bipartite=0)
        H.add_nodes_from(right, bipartite=1)
        for u in left:
            for v in right:
                if random.random() < 0.3:
                    H.add_edge(u, v)
        # garantir connexité
        if not nx.is_connected(H):
            for u in left:
                for v in right:
                    H.add_edge(u, v)
                    if nx.is_connected(H):
                        break
                if nx.is_connected(H):
                    break
    if 'planar' in classes:
        while not nx.is_planar(H):
            if H.number_of_edges() > 3 * H.number_of_nodes() - 6:
                e = random.choice(list(H.edges()))
                H.remove_edge(e[0], e[1])
            else:
                # remplacer par une grille
                n = H.number_of_nodes()
                r = int(n ** 0.5)
                H = nx.grid_2d_graph(r, r + 1 if r * (r + 1) >= n else r)
                H = nx.convert_node_labels_to_integers(H)
                break
    return H