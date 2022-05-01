import pandas as pd
import networkx as nx
import random
from main import load_data, build_graph


if __name__ == '__main__':
    instaglam0, instaglam_1, spotifly = load_data()
    artists_to_promote = [144882, 194647, 511147, 532992]

    G_0 = build_graph(instaglam0)
    G_1 = build_graph(instaglam=instaglam_1)

    hist = {}
    max_degree = sorted(G_1.degree, key=lambda x: x[1], reverse=True)[0][1]
    for i in range(max_degree+1):
        hist[i] = 0

    for ed in G_0.edges:
        if ed not in G_1.edges:  # means that edge was formed between t=-1 and t=0
            x = ed[0]
            y = ed[1]
            common_num = len(set((nx.common_neighbors(G_1, x, y))))
            hist[common_num] += 1
    total_new_edges = sum(hist.values())

    for i in range(max_degree+1):
        hist[i] = hist[i]/total_new_edges

    print(hist)
    print(sum(hist.values()))

