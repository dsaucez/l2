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
       hosts: information about hosts
       flows: information about flows
    """
    def __init__(self):
       """
       Initialize the topology with an empty graph and set of paths
       """
       self.G = nx.Graph()
       self.paths = Paths(self.G)
       self.reset()
       self.hosts = dict()
       self.flows = dict()

    def reset(self):
       """
       Recompute minimum spanning tree and reset paths
       """
       self.T = nx.minimum_spanning_tree(self.G)
       self.paths.reset()
