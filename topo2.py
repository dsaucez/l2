#!/usr/bin/python

# Copyright 2013-present Barefoot Networks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import TCLink, Intf

from p4_mininet import P4Switch, P4Host

import argparse
from time import sleep
import os
import subprocess

parser = argparse.ArgumentParser(description='Mininet demo')
parser.add_argument('--behavioral-exe', help='Path to behavioral executable',
                    type=str, action="store", required=True)
parser.add_argument('--json', help='Path to JSON config file',
                    type=str, action="store", required=True)
parser.add_argument('--cli', help='Path to BM CLI',
                    type=str, action="store", required=True)
parser.add_argument('--thrift-port', help='Thrift server port for table updates',
                    type=int, action="store", required=True)

args = parser.parse_args()

import networkx as nx
from networkx.readwrite import json_graph
import json
G_json = {'directed': False,
          'graph': {},
          'nodes': [
             {u'type': 'switch', 'id': 's13', 'thrift_ip': '127.0.0.1', u'thrift_port': 47013, "API": "http://127.0.0.1:8013"},
             {u'type': 'switch', 'id': 's12', 'thrift_ip': '127.0.0.1', u'thrift_port': 47012, "API": "http://127.0.0.1:8012"},
             {u'type': 'switch', 'id': 's11', 'thrift_ip': '127.0.0.1', u'thrift_port': 47011, "API": "http://127.0.0.1:8011"},
             {u'ip': '192.0.2.21', u'type': 'host', 'id': 'h21'},
             {u'type': 'switch', 'id': 's14', 'thrift_ip': '127.0.0.1', u'thrift_port': 47014, "API": "http://127.0.0.1:8014"},
             {u'type': 'switch', 'id': 's22', 'thrift_ip': '127.0.0.1', u'thrift_port': 47022, "API": "http://127.0.0.1:8022"},
             {u'type': 'switch', 'id': 's23', 'thrift_ip': '127.0.0.1', u'thrift_port': 47023, "API": "http://127.0.0.1:8023"},
             {u'type': 'switch', 'id': 's21', 'thrift_ip': '127.0.0.1', u'thrift_port': 47021, "API": "http://127.0.0.1:8021"},
             {u'type': 'switch', 'id': 's24', 'thrift_ip': '127.0.0.1', u'thrift_port': 47024, "API": "http://127.0.0.1:8024"},
             {u'ip': '192.0.2.11', u'type': 'host', 'id': 'h11'},
             {'ip': '192.0.2.22', 'type': 'host', 'id': 'h22'}, 
             {u'ip': '192.0.2.12', u'type': 'host', 'id': 'h12'}],
          'links': [
             {'source': 0, 'target': 2},
             {'source': 0, 'target': 4},
             {'source': 1, 'target': 2},
             {'source': 1, 'target': 4},
             {'source': 2, 'target': 11},
             {'source': 2, 'target': 9},
             {'source': 3, 'target': 7},
             {'source': 4, 'target': 8},
             {'source': 5, 'target': 7},
             {'source': 5, 'target': 8},
             {'source': 6, 'target': 7},
             {'source': 6, 'target': 8},
             {'source': 7, 'target': 10}],
          'multigraph': False} 
G = json_graph.node_link_graph(G_json)


_configs = dict()

class MyTopo(Topo):
    """
    """
    def port_id(self, sw):
        pid = 1
        if sw not in self._ports.keys():
            self._ports[sw] = pid
        else:
            pid = self._ports[sw] + 1
            self._ports[sw] = pid
        return pid

    def _make_port(self, s, port, connected_to_host):
              _port = dict()
              _port["index"] = port
              _port["name"] = "%s-eth%d" % (s, port)
              _port["edge"] = connected_to_host

              self._randomip = self._randomip + 1
              _mac = "1e:de:ad:de:ad:%x" % self._randomip
              _port["mac"] = _mac
              _port["ip"] = "198.51.100.%d" % self._randomip
              _port["prefix"] = "198.51.100.0/24"

              _configs[s]["ports"].append(_port)


    def __init__(self, sw_path, json_path, thrift_port, **opts):
        # Initialize topology and default options
        Topo.__init__(self, **opts)
      
 
        self._ports = dict()
        # collection of switches
        _nodes = dict()
        # add all switches
        for n in G.nodes():
           if G.node[n]["type"]=="switch":
               print "CREATE switch", n, G.node[n]['thrift_port']
               _n = self.addSwitch(n, sw_path = sw_path,json_path = json_path,thrift_port = G.node[n]['thrift_port'],pcap_dump = True)

               # create the configuration for the switch
               _configs[n] = dict()
               _configs[n]["switch_name"] = n
               _configs[n]["controller_ip"] = "127.0.0.1"
               _configs[n]["controller_port"] = 8000
               _configs[n]["thrift_ip"] = G.node[n]['thrift_ip']
               _configs[n]["thrift_port"] = G.node[n]['thrift_port']
               _configs[n]["API"] = G.node[n]['API']
               _configs[n]["cpu_iface"] = "cpu-veth-%s" %(n)
               _configs[n]["ports"] = list()

           if G.node[n]["type"]=="host":
               print "CREATE node " , n, G.node[n]["ip"]
               _n = self.addHost(n, ip = G.node[n]["ip"])
               print "\t", _n
           _nodes[n] = _n

        # connect nodes

        self._randomip = 0
        for s,d in G.edges():
           self.addLink(_nodes[s], _nodes[d])
           # for later use, need to know the port id used
           sport = self.port_id(s)
           dport = self.port_id(d)
           print "CONNECT %s-eth%d -> %s-eth%d" % (s, sport, d, dport)
           if G.node[s]["type"] == "switch":
               self._make_port(s, sport, G.node[d]["type"] == "host")
           if G.node[d]["type"] == "switch":
               self._make_port(d, dport, G.node[s]["type"] == "host")
           G.edge[s][d][s] = sport
           G.edge[s][d][d] = dport
           print "\t\t ", G.edge[s][d]

        for s in _configs.keys():
           _filename = "config/%s.json" % (s)
           print _filename
           with open(_filename, 'w') as _f:
               json.dump(_configs[s], _f)

def main():
    topo = MyTopo(args.behavioral_exe,
                  args.json,
                  args.thrift_port)

    net = Mininet(topo = topo,
                  host = P4Host,
                  switch = P4Switch,
                  controller = None)
    # == CPU interfaces
    # create an interface for the CPU on s11 and install it as port 11
    for s in [n for n in G.nodes() if G.node[n]["type"] == "switch"]:
        _port = _configs[s]["cpu_iface"]
        print "ADD PORT %s on %s" % (_port, s)
        cpu_intf = Intf(_port, net.get(s), 11)

    net.start()
    net.startTerms() 
    # default route to gateway for each host on eth0
    # in s1 network
    for h in [net.get(n) for n in G.nodes() if G.node[n]["type"] == "host"]:
       print "LETS config ", h
       h.setDefaultRoute("dev eth0 via 192.0.2.1") # set the default route
       h.cmd("./beat.sh &")    # launch heart beat on every host

    for s in [net.get(n) for n in G.nodes() if G.node[n]["type"] == "switch"]:
       cmd = "python lldpmain.py config/%s.json 2> log/lldp.%s.err &" % (str(s), str(s))
       print "LLDP on ", s, cmd
       s.cmd(cmd)  # launch LLDP
       
    for n in [n for n in G.nodes() if G.node[n]["type"] == "host"]:
        h = net.get(n)
        h.describe()

    sleep(1)

    # prepare switches
    for port in [ G.node[n]["thrift_port"]  for n in G.nodes() if G.node[n]["type"] == "switch" ]:
        print  "configure CLI ", port
        cmd = [args.cli, args.json, str(port)]
        with open("commands2.txt", "r") as f:
            print " ".join(cmd)
            try:
                output = subprocess.check_output(cmd, stdin = f)
                print output
            except subprocess.CalledProcessError as e:
                print e
                print e.output

    sleep(1)

    os.system("./switches.sh")

    sleep(12) 

    CLI( net )
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    main()
