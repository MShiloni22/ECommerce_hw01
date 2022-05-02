import pandas as pd
import networkx as nx
import random
from main import load_data, build_graph


if __name__ == '__main__':
    instaglam0, instaglam_1, spotifly = load_data()
    artists_to_promote = [144882, 194647, 511147, 532992]

    G_0 = build_graph(instaglam0)
    G_1 = build_graph(instaglam=instaglam_1)
