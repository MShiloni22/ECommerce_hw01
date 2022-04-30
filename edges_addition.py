import pandas as pd
import networkx as nx
import random
from main import load_data, build_graph


if __name__ == '__main__':
    instaglam0, instaglam_1, spotifly = load_data()
    artists_to_promote = [144882, 194647, 511147, 532992]

    G_0 = build_graph(instaglam0)
    G_1 = build_graph(instaglam=instaglam_1)

    for node in G_0.nodes:
        # proof that this is legitimate probability
        print(f"in time=0: {G_0.degree(node)}, in time=-1: {G_1.degree(node)}, "
              f"prob = {(G_0.degree(node) - G_1.degree(node))/G_0.degree(node) + G_1.degree(node)/G_1.number_of_nodes()}")
