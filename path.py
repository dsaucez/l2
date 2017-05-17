class Path:
    """
    Defines a generator of path selection for a given path
    """
    def __init__(self, paths):
       """
       Initializes a path composed of multiple `paths`

       :param paths: all the equal paths for the path
       :paths type: list of paths
       """
       self.paths = paths
       self.i = 0
  
    def get(self):
       """
       Returns one path in the list of paths (Round Robin)
       
       :return: a path
       """
       self.i = (self.i + 1) % len(self.paths)
       return self.paths[self.i]

