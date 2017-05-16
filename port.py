class Port:
    """
    Define a switch port
    Attributes:
       name#string cannonical name of the switch
       mac#string  MAC address of the port
       ip#string   IP address of the port
       index#int   index number of the port
       edge#Boolean whether the port is at the edge or not (connected to a host)
    """
    def __init__(self, name, mac, ip, prefix, index, edge):
       """
       Initialize a switch port
 
       :param name: cannonical name of the switch
       :type name: string

       :param mac: MAC address of the port
       :type mac: string

       :param ip: IP address of the port
       :type ip: string

       :param prefix: CIDR prefix of the port
       :type prefix: string

       :param index: index number of the port
       :type index: int

       :param edge: indicates if the port is a edge port (i.e., connected to a
                    host) or not (i.e., connected to a switch)
       :type edge: Boolean
       """
       self.name = name
       self.mac = mac
       self.ip = ip
       self.prefix = prefix
       self.index = index
       self.edge = edge

    def __str__(self):
       """
       Representation of the port as "<index>%d: <name>%s <mac>%s <ip>%s"

       :return: string representation of the port
       """
       return "%d: %s %s %s" % (self.index, self.name, self.mac, self.ip)
