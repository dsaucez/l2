from scapy.layers.l2 import sendp
import time
import sys


from lldp import create_lldp_packet

import json

# == sanity checks
if len(sys.argv) != 2:
   print "usage %s <configuration file>" % (sys.argv[0])
   exit(-1)
filename = sys.argv[1]

def send_packet(packet, interface):
    sendp(packet, verbose=False, iface=interface)


def main(filename):
    with open(filename) as data_file:
       data = json.load(data_file)

       switch_name = str(data["switch_name"])
       ports = data["ports"]
       
       while True:
           for port in ports:
               print str(port["mac"]), " ", str(port["index"]), "on", str(port["name"])
               packet = create_lldp_packet(mac_addr = port["mac"], switch_name = switch_name, port_id = str(port["index"]))
               send_packet(packet, str(port["name"]))
           time.sleep(10)

main(filename)
