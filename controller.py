# General
import json
import time
import uuid
import random

# REST API
import tornado.httpserver
import tornado.ioloop
import tornado.web
import requests

# Routing
import networkx as nx
from networkx.readwrite import json_graph

# Project
from flow import Flow
from host import Host
from topology import Topology
import command

# Constants
PORT = 8000

# For class abstraction
import abc

class RESTRequestHandlerRouting(tornado.web.RequestHandler):
    __metaclass__  = abc.ABCMeta

    def initialize(self, topology):
        self.topology = topology

    def pushCommands(self, node, cmds):
        """
        :param node: node where to push the commands
        :type node: string

        :param cmd: commands to be executed on the node
        :type cmd: list of strings
        """
        for cmd in cmds:
           push_command(self.topology.G, node, cmd)

    @abc.abstractmethod
    def _routing(self, switch, flow):
        """
	This method optimizes the routing of `flow` in the network upon
        packet_in reception from `switch`

        :param switch: switch name
        :type switch: string

        :param flow: Flow information
        :type flow: Flow

        :return: the list of commands to be executed
        """

    def post(self):
        self.set_header("Content-Type", 'application/json; charset="utf-8"')
        switch = self.request.headers.get("X-switch-name")
        params = json.loads(self.request.body.decode())

        # get the flow to optimize
        flow = Flow(dic=params)

        # call the optimization
        try:
            commands = self._routing(switch, flow)
            _resp = {"commands":commands}
        except Exception as e:
            print "Error in optimization", e
            self.set_status(304)
            self.finish()
            return

        # provide the MAC:PORT to the requesting switch
        self.set_status(200)
        self.finish(json.dumps(_resp))


######################### LINK
class RESTRequestHandlerLink(tornado.web.RequestHandler):
    def initialize(self, topology):
        self.topology = topology

    def post(self):
        self.set_header("Content-Type", 'application/json; charset="utf-8"')
        switch = self.request.headers.get("X-switch-name")
        params = json.loads(self.request.body.decode())

        _s = params["src"]
        _d = params["dst"]

        # add the node unknown.
        if not self.topology.G.has_node(params["name"]):
           self.topology.G.add_node(params["name"])
           self.topology.reset()

        # update node information
        self.topology.G.node[params["name"]]["API"] = params["API"]
        self.topology.G.node[params["name"]]["thrift_port"] = params["thrift_port"]
        self.topology.G.node[params["name"]]["thrift_ip"] = params["thrift_ip"]

        # ignore local or links we already know
        if _s == _d or self.topology.G.has_edge(_s,_d):
           self.set_status(200)
        # add the link to the topology
        else:
           self.set_status(201)
           self.topology.G.add_edge(_s, _d, attr_dict={_s:params[_s], _d:params[_d]})
           self.topology.reset()
           print "Learned link %s - %s" % (_s, _d)
           if len(self.topology.hosts) == 4 and len(self.topology.G.edges()) == 9:
              print "READY: topology discovered!"

        self.finish()

def push_command(G, node, cmd):
    _url = "%s/commands" % (str(G.node[node]["API"]))
    _body = {"thrift_ip": G.node[node]["thrift_ip"], "thrift_port": G.node[node]["thrift_port"], "commands":[cmd]}
    print "\tSend %s to _url %s" % (json.dumps(_body), _url)
    response = requests.post(_url, data = json.dumps(_body), headers={"Content-Type": "application/json"})

######################### HOST
class RESTRequestHandlerHost(tornado.web.RequestHandler):
    def initialize(self, topology):
        self.topology = topology

    # POST /host
    def post(self):
        self.set_header("Content-Type", 'application/json; charset="utf-8"')
        switch = self.request.headers.get("X-switch-name")
        params = json.loads(self.request.body.decode())
        print "Discovered %s from %s with %s" % (params["ip"], switch, params["mac"])

        host = None
        # host already known
        if params["ip"] in self.topology.hosts.keys():
           self.set_status(200)
           host = self.topology.hosts[params["ip"]]
           host.update(mac = params["mac"], switch = params["switch"], switch_port = params["switch_port"])
        # host just discovered
	else:
           self.set_status(201)
           host = Host(ip = params["ip"], mac = params["mac"], switch = params["switch"], switch_port = params["switch_port"])
           self.topology.hosts[params["ip"]] = host

           if len(self.topology.hosts) == 4 and len(self.topology.G.edges()) == 9:
              print "READY: topology discovered!"

        # return the uuid for later use
        result = {"uuid":str(host.uuid)}
        self.finish(json.dumps(result))

    # GET /host/ip
    def get(self, ip):
        self.set_header("Content-Type", 'application/json; charset="utf-8"')
        switch = self.request.headers.get("X-switch-name")

        # if the host is known, return its informations
        if ip in self.topology.hosts.keys():
           self.set_status(200)
           host = self.topology.hosts[ip]
           _host = host.attributes()
           _mac = _host["mac"]

           # push information in the intermediate switches on the spanning tree
	   
           # get the path from the requester to the requested on the spanning
	   # tree
           _first_hop = switch
           _last_hop = _host["switch"]
           _path = nx.shortest_path(self.topology.T, _first_hop, _last_hop)

           # for every switch on the path, add the MAC:PORT entry
           print "Update the path:"
           for i in range(0, len(_path)-1):
              _src = _path[i]
              _neighbor = _path[i+1]
              _portid = self.topology.T.edge[_src][_neighbor][_src]
	      # provide the port in the answer for the requester (in order to
	      # be the last getting the information
              if i == 0:
                  _host["forward_port"] = _portid
              # push the MAC:PORT on the other switches on the path
              else:
                  try:
                      _cmd = command.macPort(_mac, _portid)
                      print "Nope ---------------", _cmd
                      push_command(self.topology.T, _src, _cmd)
                  except Exception as e:
                      print "Error with southbound 1", e
           self.finish(json.dumps(_host))
        # if unknown return an error
        else:
           self.set_status(204)
           self.finish()

def main(routing_handler):
    # Topology state
    topology = Topology()

    # launch server
    rest_app = tornado.web.Application([
               ("/host", RESTRequestHandlerHost, dict(topology=topology)),
               ("/host/(.*)", RESTRequestHandlerHost, dict(topology=topology)),
               ("/optimal", routing_handler, dict(topology=topology)),
               ("/link", RESTRequestHandlerLink, dict(topology=topology))
               ])
    rest_server = tornado.httpserver.HTTPServer(rest_app)
    rest_server.listen(PORT)
    tornado.ioloop.IOLoop.current().start()

if __name__ == '__main__':
    main(RESTRequestHandlerRouting)
