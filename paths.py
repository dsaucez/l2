import networkx as nx
from path import Path

class Paths:
    """
    Maintain states about the paths optimized in order to not recompute all
    shortest paths every time as path is requested
    """
    def __init__(self, G):
        """
        Initialize the class

        :param G: topology graph 
        :type G: networkx.classes.graph.Graph
        """
        self.G = G
        self.reset()

    def reset(self):
        """
	Reset the state (forget every computation done in the past)
        """
        self.paths = dict()

    def onePath(self, src, dst):
        """
        Get one paths between `src` and `dst`
        
        :param src: source of the path
        :type src: string

        :param dst: target of the path
        :type dst: string

        :return: one path between `src` and `dst`
        """
        key = str((src, dst))
	# if the path has already been computed, get the generator
        if key in self.paths.keys():
            path = self.paths[key]
        # otherwise, generate the paths from `src` to `dst`
        else:
            _paths = nx.all_shortest_paths(self.G, src, dst)
            _array_paths = [p for p in  _paths]
            path = Path(_array_paths)
            self.paths[key] = path
        
        # get one path
        return path.get()
