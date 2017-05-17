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

# =====
topology = Topology()

# #################################  
hosts = dict()
flows = dict()
PORT = 8000


class RESTRequestHandlerOptimization(tornado.web.RequestHandler):
    def initialize(self, hosts, flows, topology):
        self.hosts = hosts
        self.flows = flows
        self.topology = topology

    def post(self):
        self.set_header("Content-Type", 'application/json; charset="utf-8"')
        switch = self.request.headers.get("X-switch-name")
        params = json.loads(self.request.body.decode())

        # get the flow to optimize
        flow = Flow(dic=params)
        _flow = str(flow)
        if _flow in self.flows.keys():
           print ">>>>>>>>>>> already optimal here from %s for %s" % (switch, _flow)
           self.set_status(304)
           self.finish()
           return
        self.flows[_flow] = True

        # impossible to optimize if unknown destination
        if flow.dstAddr not in self.hosts.keys():
           self.set_status(204)
           self.finish()
           return

        # from what switch to what switch?
        _src = switch
        _dst = self.hosts[flow.dstAddr].switch
        _mac = self.hosts[flow.dstAddr].mac

        # pick one path 
        _path = self.topology.paths.onePath(_src, _dst)

	# compute the port to use on each switch on the (_src, _dst) path
        print "Compute optimal path:"
        _resp = {"commands":list()}
        for i in range(0, len(_path)):
            _src = _path[i]
	    # For the switch connected to the host, get the port to the host
            if i == len(_path) - 1:
               _portid = self.hosts[flow.dstAddr].switch_port 
	    # For switches on the path to the host, get the port to the
	    # next-hop
            else:
                _neighbor = _path[i+1]
                _portid = self.topology.G.edge[_src][_neighbor][_src]
            # Command to run on the switch to add the flow
            _cmd = "table_add flow_table set_fast_forward %s => %d" % (_flow, _portid)

	    # do not push the command to the switch that made the request in
	    # order to update it last (to avoid loops)
            if i == 0:
                _resp["commands"].append(_cmd)
            # push the MAC:PORT on the other switches on the path
            else:
                try:
                    push_command(self.topology.G, _src, _cmd)
                except Exception as e:
      	            print "Error with southbound", e

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
        
        self.finish()

def push_command(G, node, cmd):
    _url = "%s/commands" % (str(G.node[node]["API"]))
    _body = {"thrift_ip": G.node[node]["thrift_ip"], "thrift_port": G.node[node]["thrift_port"], "commands":[cmd]}
    print "\tSend %s to _url %s" % (json.dumps(_body), _url)
    response = requests.post(_url, data = json.dumps(_body), headers={"Content-Type": "application/json"})

######################### HOST
class RESTRequestHandlerHost(tornado.web.RequestHandler):
    def initialize(self, hosts, topology):
        self.hosts = hosts
        self.topology = topology

    # POST /host
    def post(self):
        self.set_header("Content-Type", 'application/json; charset="utf-8"')
        switch = self.request.headers.get("X-switch-name")
        params = json.loads(self.request.body.decode())
        print "Discovered %s from %s with %s" % (params["ip"], switch, params["mac"])

        host = None
        # host already known
        if params["ip"] in self.hosts.keys():
           self.set_status(200)
           host = self.hosts[params["ip"]]
           host.update(mac = params["mac"], switch = params["switch"], switch_port = params["switch_port"])
        # host just discovered
	else:
           self.set_status(201)
           host = Host(ip = params["ip"], mac = params["mac"], switch = params["switch"], switch_port = params["switch_port"])
           self.hosts[params["ip"]] = host

        # return the uuid for later use
        result = {"uuid":str(host.uuid)}
        self.finish(json.dumps(result))

    # GET /host/ip
    def get(self, ip):
        self.set_header("Content-Type", 'application/json; charset="utf-8"')
        switch = self.request.headers.get("X-switch-name")

        # if the host is known, return its informations
        if ip in self.hosts.keys():
           self.set_status(200)
           host = self.hosts[ip]
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
                      _cmd = "table_add mac_table set_out_port %s => %d" % (_mac, _portid)
                      push_command(self.topology.T, _src, _cmd)
                  except Exception as e:
                      print "Error with southbound", e
           self.finish(json.dumps(_host))
        # if unknown return an error
        else:
           self.set_status(204)
           self.finish()

# launch server
rest_app = tornado.web.Application([
           ("/host", RESTRequestHandlerHost, dict(hosts=hosts,topology=topology)),
           ("/host/(.*)", RESTRequestHandlerHost, dict(hosts=hosts,topology=topology)),
           ("/optimal", RESTRequestHandlerOptimization, dict(hosts=hosts,flows=flows,topology=topology)),
           ("/link", RESTRequestHandlerLink, dict(topology=topology))
           ])
rest_server = tornado.httpserver.HTTPServer(rest_app)
rest_server.listen(PORT)
tornado.ioloop.IOLoop.current().start()
