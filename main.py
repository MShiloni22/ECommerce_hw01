import sys
import networkx as nx
import random
import pandas as pd


def load_data():
    instaglam_1 = pd.read_csv('./instaglam_1.csv')
    instaglam0 = pd.read_csv('./instaglam0.csv')
    spotifly = pd.read_csv('./spotifly.csv')
    return instaglam0, instaglam_1, spotifly


def build_graph(instaglam):
    """
    build network graph and set relevant attributes for each node
    :param instaglam: description of friendships between members in the network (pd.Dataframe)
    :return: network graph (nx.Graph)
    """
    G = nx.Graph()
    # extract all nodes
    users = set(instaglam['userID'].values)
    friends = set(instaglam['friendID'].values)
    members = users.union(friends)
    # add edges between nodes
    for m in members:
        G.add_node(m)
    for i, j in zip(instaglam['userID'].values, instaglam['friendID'].values):
        G.add_edge(i, j)
    # set nodes attributes. test attributes are used in calculations of IC
    nx.set_node_attributes(G, 0, name="buying probability")
    nx.set_node_attributes(G, False, name="infected")
    nx.set_node_attributes(G, 0, name="buying probability test")
    nx.set_node_attributes(G, False, name="infected test")
    nx.set_node_attributes(G, 0, name="h")
    return G


def calc_buying_probability(G, nodes_group, test_flag=False):
    """
    For each node in nodes_group, calculate and update the probability that it will buy the product according to
    the given formula.
    :param G: network graph
    :param nodes_group: set of nodes for which we would like to find the buying probability
    :param test_flag: boolean. True if the calculation is done for IC calculation, else False.
    :return: None (only updating attributes of nodes)
    """
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
    influence cone algorithm
    :param S: set of nodes
    :param G: graph
    :return: influence cone rank of S
    """
    influence_cone = len(S)
    for s in S:
        G.nodes[s]["infected test"] = True
    neighbors_of_S = set([n for s in S for n in G.neighbors(s)])
    calc_buying_probability(G, neighbors_of_S, test_flag=True)
    for n in neighbors_of_S:
        influence_cone += G.nodes[n]["buying probability test"]
    for s in S:
        G.nodes[s]["infected test"] = False  # clean attribute for the next runs
    return influence_cone


def hill_climbing(G, k):
    """
    Algorithm to find k influencers in graph G
    :param G: network graph
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
    add new edges to graph G based on new edges probability matrix P
    :param G: network graph
    :param P: new edges probability matrix (dict)
    :return: None (add new edges to G based on P).
    """
    for i in G.nodes:
        for j in G.nodes:
            if i < j and not G.has_edge(i, j):  # saving calculation cost - the matrix is symmetric
                u = random.random()
                if u < P[(i, j)]:
                    G.add_edge(i, j)


def build_probabilities_dict(G, probability_function, hist=None):
    """
    Build matrix of new edge probability for every two nodes i, j in network graph G.
    P[(i,j)] = the probability that an edge will be formed between i, j according to G
    :param G: network graph
    :param probability_function: probability for each two nodes i, j to become friends at the network
    :param hist: relevant only if probability_function == common_neighbors_index. view this function's docstring
                 for more details.
    :return: matrix P of new edge probability for every two nodes i, j
    """
    P = dict()
    for i in G.nodes:
        for j in G.nodes:
            if i < j:  # saving calculation cost - the matrix is symmetric
                P[(i, j)] = probability_function(G_0, G_1, i, j, hist)
    return P


def friendly_index(G_0, G_1, u, v, hist=None):
    """
    An index with a sociological orientation based on the tendency of each node to create new friends based on the
    differences in the number of its friends between the previous time and the present time and the ratio of common
    friends with another node.

    The *friendly index* symbolizes the ratio between the number of new friends created to any node u on the current day
    and the number of friends it had on the previous day.

    The *popularity index* symbolizes how popular the node is in relation to others. (at the end we thought that this
    index is not much informative or models a phenomena at the real world so we gave up of using it)

    The *chance to meet* index examines, based on the mutual friends of each two nodes, whether they had a chance to
    meet and become friends as well.

    The working assumption is that a friendly node u has a greater tendency to make new friends, with friendly node v if
    the ratio of (u,v)'s mutual friends out of all the friends of the two together is large.
    :param G_0: network graph at time t=0 (today)
    :param G_1: etwork graph at time t=-1 (yesterday)
    :param u: a node
    :param v: another node
    :param hist: not relevant
    :return: probability of (u,v) to become friends today based on friendly_index.
    remark - we couldn't guarantee by proof (and it will not be true to say) that this probability is never
    greater than 1 but since in practice: u_friendly , v_friendly << 1 , chance_to_meet <= 1
    we get:
    ==> u_friendly + v_friendly < 1
    ==> (u_friendly + v_friendly) * chance_to_meet <= 1
    """

    u_friendly = (G_0.degree(u) - G_1.degree(u)) / G_0.degree(u)
    # u_popularity = G_1.degree(u) / G_1.number_of_nodes() -
    # we have also considered u_popularity may be G_1.degree(u) / G_1.node_with_max_degree, but dacided not to use
    # this popularity index as well
    v_friendly = (G_0.degree(v) - G_1.degree(v)) / G_0.degree(v)
    # v_popularity = G_1.degree(u) / G_1.number_of_nodes()
    chance_to_meet = len(set(G_1.neighbors(u)).intersection(set(G_1.neighbors(v)))) \
                     / len((set(G_1.neighbors(u)).union(set(G_1.neighbors(v)))))
    res = (u_friendly + v_friendly) * chance_to_meet
    return res


def common_neighbors_index(G_0, G_1, u, v, hist):
    """
    An index with a statistical tendency based on the number of common friends of two nodes u,v to determine the
    probability that they will become friends as well.
    The index uses a histogram that counts for each edge generated between time=-1 and time=0 the number of common
    friends that the two nodes had in time=-1.
    The probability of the formation of an edge today between two nodes that have x common members yesterday is defined
    by: prob = hist[x] / sum([hist[y] for y in range(G.node_with_max_degree)]).
    :param G_0: network today
    :param G_1: network yesterday
    :param u: a node
    :param v: another node
    :param hist: histogram that counts for each edge generated between time=-1 and time=0 the number of common
                 friends that the two nodes had in time=-1.
    :return: probability of (u,v) edge to form
    """
    common_neighbors = len(set(nx.common_neighbors(G_1, u, v)))
    return hist[common_neighbors]


def new_edges_by_commoneighbors_histogram(G_0, G_1):
    """
    helper function when using the common_neighbors_index. calculating the histogram as described in
    common_neighbors_index's docstring
    :param G_0: network today
    :param G_1: network yesterday
    :return: histogram
    """
    histogram = {}
    max_degree = sorted(G_1.degree, key=lambda x: x[1], reverse=True)[0][1]

    # initialization
    for i in range(max_degree + 1):
        histogram[i] = 0

    # fill histogram values
    for e in G_0.edges:
        if e not in G_1.edges:  # means that edge was formed between t=-1 and t=0
            u = e[0]
            v = e[1]
            common_num = len(set((nx.common_neighbors(G_1, u, v))))
            histogram[common_num] += 1

    # divide histogram values by total number of new edges between yesterday and today to form probability function
    total_new_edges = sum(histogram.values())
    for i in range(max_degree + 1):
        histogram[i] = histogram[i] / total_new_edges

    return histogram


def prob_p_forall_index(p):
    """
    very naive probability index that assigned for every (u,v) edge probability p to form
    :param p: probability to form
    :return: probability function
    """
    return lambda w, x, y, z, hist: p


if __name__ == '__main__':

    # input variables: edit these vars
    artist_to_promote = 511147  # our artists are [144882, 194647, 511147, 532992]
    new_edges_method = common_neighbors_index
    finish_without_simulation = False  # if True the simulation itself will not run (time saving)

    print(f"artist: {artist_to_promote}")
    print(f"new edges method: {new_edges_method.__name__}")

    print("loading data...")
    instaglam0, instaglam_1, spotifly = load_data()

    # build graphs
    print("building network...")
    G_1 = build_graph(instaglam_1)  # graph at time=-1
    G_0 = build_graph(instaglam0)  # graph at time=0
    for n in G_0.nodes:  # initialization of properties foreach node
        G_0.nodes[n]["buying probability"] = 0
        G_0.nodes[n]["infected"] = False
        G_0.nodes[n]["buying probability test"] = 0
        G_0.nodes[n]["infected test"] = False
        filt = (spotifly['userID'] == n) & (spotifly[' artistID'] == artist_to_promote)
        G_0.nodes[n]["h"] = 0 if spotifly.loc[filt, '#plays'].empty else list(spotifly.loc[filt, '#plays'])[0]

    # simulate creation of new edges in the graph
    G_random = nx.Graph(G_0)
    G_random_prev = nx.Graph(G_1)
    histogram = None
    if new_edges_method != prob_p_forall_index(0):
        print("simulating creation of new edges in the network...")
        for i in range(7):
            if new_edges_method != common_neighbors_index:
                P = build_probabilities_dict(G_random, probability_function=new_edges_method)
            else:
                histogram = new_edges_by_commoneighbors_histogram(G_0=G_random, G_1=G_random_prev)
                P = build_probabilities_dict(G_random, probability_function=common_neighbors_index, hist=histogram)
                G_random_prev = nx.Graph(G_random)
            add_new_edges(G_random, P)

    print("finding influencers...")
    # find influencers by running HC on the simulated graph
    influencers = hill_climbing(G_random, 5)
    print(f"influencers: {influencers}")

    infected_cnt = 5
    for influncer in influencers:
        G_0.nodes[influncer]["infected"] = True

    if finish_without_simulation:
        sys.exit("Finished without simulating")

    # simulation:
    print("simulation...")
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
        if t < 6:
            # build probabilities dict at time=t
            if new_edges_method != common_neighbors_index:
                P = build_probabilities_dict(G_0, probability_function=new_edges_method)
            else:
                P = build_probabilities_dict(G_random, probability_function=common_neighbors_index, hist=histogram)
            add_new_edges(G_0, P)
            # calc buying probability at time=t
            calc_buying_probability(G_0, G_0.nodes)
