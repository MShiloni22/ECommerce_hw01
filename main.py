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
    return G


def calc_buying_probability(G, spotifly, artistID, nodes_group, test_flag=False):
    for n in nodes_group:
        nt = G.degree(n)
        bt = len([v for v in G.neighbors(n) if G.nodes[v]["infected"]])
        filt = (spotifly['userID'] == n) & (spotifly[' artistID'] == artistID)
        h = 0 if spotifly.loc[filt, '#plays'].empty else list(spotifly.loc[filt, '#plays'])[0]
        #print(f"{nt},{bt},{h}")
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
        # if G.nodes[n]['buying probability'] > 0:
        #    print(f"{n}, {G.nodes[n]['buying probability']}")


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
        count = 0
        for v in V_difference_S:
            # print(f"i = {i}, count = {count}")
            count += 1
            S.add(v)
            IC_Sv = IC(S, G)
            S.remove(v)
            mv = IC_Sv - IC_S
            if mv > max_mv:
                max_mv = mv
                argmax_mv = v
        S.add(argmax_mv)
    # print("S:", S)
    return S


if __name__ == '__main__':
    instaglam0, instaglam_1, spotifly = load_data()
    artists_to_promote = [144882, 194647, 511147, 532992]

    G = build_graph(instaglam0)
    nx.set_node_attributes(G, 0, name="buying probability")
    nx.set_node_attributes(G, False, name="infected")
    nx.set_node_attributes(G, 0, name="buying probability test")
    nx.set_node_attributes(G, False, name="infected test")

    for artist in artists_to_promote:
        print(f"artist={artist}")
        for n in G.nodes:
            G.nodes[n]["buying probability"] = 0
            G.nodes[n]["infected"] = False

        influencers = hill_climbing(G, 5)
        infected_cnt = 5
        infected_list = [i for i in influencers]
        print(f"influencers: {influencers}\n")
        for influncer in influencers:
            G.nodes[influncer]["infected"] = True
        calc_buying_probability(G, spotifly, artist, G.nodes)
        for t in range(1, 7):
            for node in G.nodes:
                u = random.random()
                if G.nodes[node]["buying probability"] > 1 - u and G.nodes[node]["infected"] == False:
                    G.nodes[node]["infected"] = True
                    infected_cnt += 1
                    infected_list.append(node)
            calc_buying_probability(G, spotifly, artist, G.nodes)
            print(f"infected at time {t}: {infected_cnt}")
            #print(infected_list)

