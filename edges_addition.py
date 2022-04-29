import pandas as pd
import networkx as nx
import random


def load_data():
    instaglam_1 = pd.read_csv('./instaglam_1.csv')
    instaglam0 = pd.read_csv('./instaglam0.csv')
    spotifly = pd.read_csv('./spotifly.csv')
    return instaglam0, instaglam_1, spotifly


def build_graph(instaglam0):
    G = nx.Graph()
    users = set(instaglam0['userID'].values)
    friends = set(instaglam0['friendID'].values)
    members = users.union(friends)
    for m in members:
        G.add_node(m)
    for i, j in zip(instaglam0['userID'].values, instaglam0['friendID'].values):
        G.add_edge(i, j)
    nx.set_node_attributes(G, 0, name="buying probability")
    nx.set_node_attributes(G, False, name="infected")
    nx.set_node_attributes(G, 0, name="buying probability test")
    nx.set_node_attributes(G, False, name="infected test")
    return G


if __name__ == '__main__':
    instaglam0, instaglam_1, spotifly = load_data()
    artists_to_promote = [144882, 194647, 511147, 532992]

    G_0 = build_graph(instaglam0)
    G_1 = build_graph(instaglam0=instaglam_1)

    for node in G_0.nodes:
        # proof that this is legitimate probability
        print(f"in time=0: {G_0.degree(node)}, in time=-1: {G_1.degree(node)}, "
              f"prob = {(G_0.degree(node) - G_1.degree(node))/G_0.degree(node) + G_1.degree(node)/G_1.number_of_nodes()}")
