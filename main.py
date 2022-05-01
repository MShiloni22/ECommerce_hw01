import networkx as nx
import random
import pandas as pd


def load_data():
    instaglam_1 = pd.read_csv('./instaglam_1.csv')
    instaglam0 = pd.read_csv('./instaglam0.csv')
    spotifly = pd.read_csv('./spotifly.csv')
    return instaglam0, instaglam_1, spotifly


def build_graph(instaglam):
    G = nx.Graph()
    users = set(instaglam['userID'].values)
    friends = set(instaglam['friendID'].values)
    members = users.union(friends)
    for m in members:
        G.add_node(m)
    for i, j in zip(instaglam['userID'].values, instaglam['friendID'].values):
        G.add_edge(i, j)
    nx.set_node_attributes(G, 0, name="buying probability")
    nx.set_node_attributes(G, False, name="infected")
    nx.set_node_attributes(G, 0, name="buying probability test")
    nx.set_node_attributes(G, False, name="infected test")
    nx.set_node_attributes(G, 0, name="h")
    return G


def calc_buying_probability(G, nodes_group, test_flag=False):
    for n in nodes_group:
        nt = G.degree(n)
        h = G.nodes[n]["h"]
        if test_flag:
            bt = len([v for v in G.neighbors(n) if G.nodes[v]["infected test"]])
        else:
            bt = len([v for v in G.neighbors(n) if G.nodes[v]["infected"]])
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
    calc_buying_probability(G, test_group, test_flag=True)
    visited_neighbors = set()
    for s in S:
        for n in G.neighbors(s):
            if n not in visited_neighbors:
                influence_cone += G.nodes[n]["buying probability test"]
                visited_neighbors.add(n)
    for s in S:
        G.nodes[s]["infected test"] = False
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
        S.add(argmax_mv)
    return S


def add_new_edges(G: nx.Graph, P):
    """
    add new edges to graph G_0 based on new edges probability matrix P
    :param G: instaglam graph at time t=0
    :param P: new edges probability matrix (dict)
    :return: add new edges to G_0 based on P.
    """
    for i in G.nodes:
        for j in G.nodes:
            if i < j and not G.has_edge(i, j):
                u = random.random()
                if u < P[(i, j)]:
                    G.add_edge(i, j)


def build_probabilities_dict(G, probability_function, hist=None):
    P = dict()
    for i in G.nodes:
        for j in G.nodes:
            if i < j:
                P[(i, j)] = probability_function(G_0, G_1, i, j, hist)
    return P


def friendly_popularity_index(G_0, G_1, u, v, hist=None):
    u_friendly = (G_0.degree(u) - G_1.degree(u)) / G_0.degree(u)
    u_popularity = G_1.degree(u) / G_1.number_of_nodes()
    v_friendly = (G_0.degree(v) - G_1.degree(v)) / G_0.degree(v)
    v_popularity = G_1.degree(u) / G_1.number_of_nodes()
    chance_to_meet = len(set(G_1.neighbors(u)).intersection(set(G_1.neighbors(v)))) / len((set(G_1.neighbors(u)).union(set(G_1.neighbors(v)))))
    # print(f"chance = {chance_to_meet}")
    res = (u_friendly + v_friendly) * chance_to_meet
    # print(f"res = {res}")
    return res


def common_neighbors_index(G_0, G_1, u, v, hist):

    """hist = {}
    max_degree = sorted(G_1.degree, key=lambda x: x[1], reverse=True)[0][1]
    for i in range(max_degree + 1):
        hist[i] = 0

    for ed in G_0.edges:
        if ed not in G_1.edges:  # means that edge was formed between t=-1 and t=0
            x = ed[0]
            y = ed[1]
            common_num = len(set((nx.common_neighbors(G_1, x, y))))
            hist[common_num] += 1
    total_new_edges = sum(hist.values())

    for i in range(max_degree + 1):
        hist[i] = hist[i] / total_new_edges"""
    common_neighbors = len(set(nx.common_neighbors(G_1, u, v)))
    return hist[common_neighbors]


def create_hist(G_0, G_1):
    hist = {}
    max_degree = sorted(G_1.degree, key=lambda x: x[1], reverse=True)[0][1]
    for i in range(max_degree + 1):
        hist[i] = 0

    for ed in G_0.edges:
        if ed not in G_1.edges:  # means that edge was formed between t=-1 and t=0
            x = ed[0]
            y = ed[1]
            common_num = len(set((nx.common_neighbors(G_1, x, y))))
            hist[common_num] += 1
    total_new_edges = sum(hist.values())

    for i in range(max_degree + 1):
        hist[i] = hist[i] / total_new_edges

    return hist


if __name__ == '__main__':

    instaglam0, instaglam_1, spotifly = load_data()
    # if we run the simulation for each artist separately we get better results. why?
    artists_to_promote = [144882, 194647, 511147, 532992]

    G_0 = build_graph(instaglam0)
    G_1 = build_graph(instaglam_1)
    G_random_test = nx.Graph(G_0)
    G_random_prev = nx.Graph(G_1)

    # simulate creation of new edges
    for i in range(7):
        #P = build_probabilities_dict(G_random_test, probability_function=lambda w, x, y, z: 0.001)
        #P = build_probabilities_dict(G_random_test, probability_function=friendly_popularity_index)
        hist = create_hist(G_0=G_random_test, G_1=G_random_prev)
        P = build_probabilities_dict(G_random_test, probability_function=common_neighbors_index, hist=hist)
        G_random_prev = nx.Graph(G_random_test)
        add_new_edges(G_random_test, P)


    # todo: think how to factorize elements of friendly_popularity_index since we would like to factor the number of
    #  edges at each iter by 14324 / 12712 =~ 1.12 
    print("G_1: ", G_1)  # 12712 edges
    print("G_0: ", G_0)  # 14324 edges
    print("G_random_test: ", G_random_test)  # 15127 edges

    # initialization of properties foreach node
    for artist in artists_to_promote:
        print(f"artist={artist}")
        for n in G_0.nodes:
            G_0.nodes[n]["buying probability"] = 0
            G_0.nodes[n]["infected"] = False
            G_0.nodes[n]["buying probability test"] = 0
            G_0.nodes[n]["infected test"] = False
            filt = (spotifly['userID'] == n) & (spotifly[' artistID'] == artist)
            G_0.nodes[n]["h"] = 0 if spotifly.loc[filt, '#plays'].empty else list(spotifly.loc[filt, '#plays'])[0]

        influencers = hill_climbing(G_random_test, 5)
        print(f"influencers: {influencers}")
        infected_cnt = 5
        for influncer in influencers:
            G_0.nodes[influncer]["infected"] = True

        # calc buying probability at time=0
        calc_buying_probability(G_0, G_0.nodes)

        # start simulation on network at time=0, do 6 iterations
        for t in range(1, 7):
            # check foreach node if it got infected
            for node in G_0.nodes:
                u = random.random()
                if G_0.nodes[node]["buying probability"] > u and G_0.nodes[node]["infected"] is False:
                    G_0.nodes[node]["infected"] = True
                    infected_cnt += 1
            print(f"infected at time {t}: {infected_cnt}")
            # add new edges to graph according probability function
            #P = build_probabilities_dict(G_0, probability_function=lambda w, x, y, z: 0.001)
            P = build_probabilities_dict(G_random_test, probability_function=common_neighbors_index, hist=hist)
            add_new_edges(G_0, P)
            # calc buying probability at time=t
            calc_buying_probability(G_0, G_0.nodes)
        print()
