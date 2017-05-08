from scapy.packet import *
from scapy.fields import *

class CPUHeader(Packet):
    name = "CPUHeader"
    fields_desc = [
               LongField("preamble", 0),
               ShortField("ifIndex", 0),
               ShortField("etherType", 0)]
