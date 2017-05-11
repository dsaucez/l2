class Flow:
    """
    Define a 5-tuple data-plane flow
    Attributes:
       srcAddr#string source address
       dstAddr#string destination address
       protocol#int   protocol
       srcPort#int    source port
       dstPort#int    destination port
    """
    def __init__(self, srcAddr=None, dstAddr=None, protocol=None, srcPort=None, dstPort=None, dic=None):
       """
       Initialize a data-plane flow base on its 5-tuple
 
       :param srcAddr: source IP address
       :type srcAddr: string

       :param dstAddr: destination IP address
       :type dstAddr: string

       :param protocol: protocol
       :type protocol: int

       :param srcPort: source port
       :type srcPort: int

       :param dstPort: destination port 
       :type dstPort: int
       """
       if dic is None:
          self.srcAddr = srcAddr
          self.dstAddr = dstAddr
          self.srcPort = srcPort
          self.dstPort = dstPort
          self.protocol = protocol
       else:
          self.srcAddr = dic["srcAddr"]
          self.dstAddr = dic["dstAddr"]
          self.srcPort = dic["srcPort"]
          self.dstPort = dic["dstPort"]
          self.protocol = dic["protocol"]

    def attributes(self):
       return {
           "srcAddr" : self.srcAddr,
           "dstAddr" : self.dstAddr,
           "srcPort" : self.srcPort,
           "dstPort" : self.dstPort,
           "protocol" : self.protocol
       }

    def __hash__(self):
       return self.__str__().__hash__()

    def __eq__(self, other):
       return self.__hash__() == other.__hash__()

    def __str__(self):
       """
       representation of the 5-tuple flow as "<source address>%s <destination address>%s <protocol>%d <source port>%d <destination port>%d"

       :return: 5-tuple flow representation
       """
       return "%s %s %d %d %d" % ((self.srcAddr, self.dstAddr, self.protocol, self.srcPort, self.dstPort))

