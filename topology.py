# routing
import networkx as nx

# Project
from paths import Paths

class Topology:
    """
    Provides methods to work on topology related features
   
    Attribues:
       G: graph of the network
       T: minimum spanning tree of the network
       paths: collection of paths
    """
    def __init__(self):
       self.G = nx.Graph()
       self.paths = Paths(self.G)
       self.reset()

    def reset(self):
       self.T = nx.minimum_spanning_tree(self.G)
       self.paths.reset()
