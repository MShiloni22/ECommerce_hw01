import networkx
import numpy as np
import networkx as nx
import random
import pandas as pd


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


def calc_buying_probability(G, spotifly, artistID, nodes_group, test_flag=False):
    for n in nodes_group:
        nt = G.degree(n)
        if test_flag:
            bt = len([v for v in G.neighbors(n) if G.nodes[v]["infected test"]])
        else:
            bt = len([v for v in G.neighbors(n) if G.nodes[v]["infected"]])
        filt = (spotifly['userID'] == n) & (spotifly[' artistID'] == artistID)
        h = 0 if spotifly.loc[filt, '#plays'].empty else list(spotifly.loc[filt, '#plays'])[0]
        if test_flag:
            if h == 0:
                G.nodes[n]["buying probability test"] = bt / nt
            else:
                G.nodes[n]["buying probability test"] = ((h * bt) / (1000 * nt))
        else:
            if h == 0:
                G.nodes[n]["buying probability"] = bt / nt
            else:
                G.nodes[n]["buying probability"] = ((h * bt) / (1000 * nt))


def IC(S, G):
    """
    influence cone
    :param S: set of nodes
    :param G: graph
    :return: influence cone rank of S
    """
    influence_cone = len(S)
    for s in S:
        G.nodes[s]["infected test"] = True
    test_group = set([j for s in S for j in G.neighbors(s)])
    # print("test_group:", test_group)
    calc_buying_probability(G, spotifly, artist, test_group, test_flag=True)
    visited_neighbors = set()
    for s in S:
        for n in G.neighbors(s):
            if n not in visited_neighbors:
                influence_cone += G.nodes[n]["buying probability test"]
                visited_neighbors.add(n)
    for s in S:
        G.nodes[s]["infected test"] = False
    # print("IC =", influence_cone)
    return influence_cone


def hill_climbing(G, k):
    """
    find best k influencers
    :param G: graph
    :param k: number of wanted influencers
    :return: set S of k influencers
    """
    S = set()
    for i in range(k):
        argmax_mv = None
        max_mv = -1
        IC_S = IC(S, G)
        V_difference_S = set(G.nodes).difference(S)
        for v in V_difference_S:
            S.add(v)
            IC_Sv = IC(S, G)
            S.remove(v)
            mv = IC_Sv - IC_S
            if mv > max_mv:
                max_mv = mv
                argmax_mv = v
                # print(f"We have a new max = {max_mv} and new argmax_mv = {argmax_mv}. This is iter {i}")
                # print(f"argmax {argmax_mv} has {G.degree(argmax_mv)}")
        S.add(argmax_mv)
    # print("S:", S)
    return S


def add_new_edges(G: networkx.Graph, P):
    """
    add new edges to graph G based on new edges probability matrix P
    :param G: instaglam graph at time t=0
    :param P: new edges probability matrix (dict)
    :return: add new edges to G based on P.
    """
    for i in G.nodes:
        for j in G.nodes:
            if i < j and not G.has_edge(i, j):
                u = random.random()
                if u < P[(i, j)]:
                    G.add_edge(i, j)


def build_probabilities_dict(G, probability_function):
    P = dict()
    for i in G.nodes:
        for j in G.nodes:
            if i < j:
                P[(i, j)] = probability_function(i, j)
    return P


if __name__ == '__main__':
    instaglam0, instaglam_1, spotifly = load_data()
    artists_to_promote = [144882, 194647, 511147, 532992]

    G = build_graph(instaglam0)

    G_random_test = networkx.Graph(G)
    for i in range(7):
        P = build_probabilities_dict(G_random_test, probability_function=lambda x, y: 1 / 100)
        add_new_edges(G_random_test, P)

    for artist in artists_to_promote:
        print(f"artist={artist}")
        for n in G.nodes:
            G.nodes[n]["buying probability"] = 0
            G.nodes[n]["infected"] = False
            G.nodes[n]["buying probability test"] = 0
            G.nodes[n]["infected test"] = False

        influencers = hill_climbing(G_random_test, 5)  # every time {468812, 682482, 411093, 308470, 548221}
        #influencers = [468812, 682482, 411093, 308470, 548221]  # results: 894, 816, 756, 999
        print(f"influencers: {influencers}\n")
        infected_cnt = 5
        infected_list = [i for i in influencers]
        for influncer in influencers:
            G.nodes[influncer]["infected"] = True
        calc_buying_probability(G, spotifly, artist, G.nodes)
        for t in range(1, 7):
            for node in G.nodes:
                u = random.random()
                if G.nodes[node]["buying probability"] > u and G.nodes[node]["infected"] is False:
                    G.nodes[node]["infected"] = True
                    infected_cnt += 1
                    infected_list.append(node)
            P = build_probabilities_dict(G, probability_function=lambda x, y: 1 / 100)
            add_new_edges(G, P)
            calc_buying_probability(G, spotifly, artist, G.nodes)
            print(f"infected at time {t}: {infected_cnt}")
