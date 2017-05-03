import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.queues
import tornado.web
import json
import time
import uuid
from flow import Flow
import requests

import networkx as nx
from networkx.readwrite import json_graph

with open("topology_ctr.json", "r") as topo_file:
    G_json = json.load(topo_file)
    G = json_graph.node_link_graph(G_json)

_T = nx.minimum_spanning_tree(G)

# #################################  


class Host:
    def __init__(self, ip, mac, switch, switch_port):
        self.ip = ip
        self.mac = mac
        self.switch = switch
        self.switch_port = switch_port
        self.uuid = uuid.uuid1()

    def update(self, mac, switch, switch_port):
        self.mac = mac
        self.switch = switch
        self.switch_port = switch_port

    def __str__(self):
        return str(self.uuid)

    def attributes(self):
        return {
            "ip": self.ip,
            "mac": self.mac,
            "switch":self.switch,
            "switch_port":self.switch_port,
            "uuid": str(self.uuid),
            "local_port": -1
            }

hosts = dict()
PORT = 8000


class RESTRequestHandlerOptimization(tornado.web.RequestHandler):
    def initialize(self, hosts):
        self.hosts = hosts

    def whatPort(self, flow, switch):
        cmds = list()
#        print "PATH >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", switch
        _src = switch
        _dst = self.hosts[flow.dstAddr].switch
        _flow = str(flow)

        # go directly to the port we learned the IP
        if _src == _dst:
#           print "%s == %s" % (_src, _dst)
           cmd = "table_add flow_table set_fast_forward %s => %s %d" % (_flow, self.hosts[flow.dstAddr].mac, self.hosts[flow.dstAddr].switch_port)
           cmds.append(cmd)
        # make funky optimization
        else:
           global _T
#################           _T = nx.minimum_spanning_tree(G) ###############################################################################################
           _path = nx.shortest_path(_T, _src, _dst)
           i = 0
           _src = _path[i]
           _neighbor = _path[i+1]
           _portid = _T.edge[_src][_neighbor][_src]
           _mac = self.hosts[flow.dstAddr].mac
           cmd = "table_add flow_table set_fast_forward %s => %s %d" % (_flow, _mac, _portid)
           cmds.append(cmd)

        print "%s optimizes flow %s " % (switch, str(flow)) #cmds)
        return {"commands":cmds}

    def post(self):
#        print "Optimize flow"

        self.set_header("Content-Type", 'application/json; charset="utf-8"')
        switch = self.request.headers.get("X-switch-name")
        params = json.loads(self.request.body.decode())

        # get the flow to optimize
        flow = Flow(dic=params)
        
        # if we know where the IP address is, we can optimze
        if flow.dstAddr in self.hosts.keys():
           optimal = self.whatPort(flow, switch)
           self.set_status(200)
           self.finish(json.dumps(optimal))
        # otherwise, we can't
        else:
           self.set_status(204)
           self.finish()

######################### LINK
class RESTRequestHandlerLink(tornado.web.RequestHandler):
    def post(self):
        self.set_header("Content-Type", 'application/json; charset="utf-8"')
        switch = self.request.headers.get("X-switch-name")
        params = json.loads(self.request.body.decode())

        _s = params["src"]
        _d = params["dst"]

        # ignore local or links we already know
        if _s == _d or G.has_edge(_s,_d):
           self.set_status(200)
        else:
           self.set_status(201)
           print "Learned link %s - %s" % (_s, _d)
           G.add_edge(_s, _d, attr_dict={_s:params[_s], _d:params[_d]})
           # recompute the spanning tree
           global _T
           _T = nx.minimum_spanning_tree(G)
        
        self.finish()


######################### HOST
class RESTRequestHandlerHost(tornado.web.RequestHandler):
    def initialize(self, hosts):
        self.hosts = hosts

    # POST /host
    def post(self):
#        print "Learn host"

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
           global _T
#################           _T = nx.minimum_spanning_tree(G) ####################################################################################################
           _path = nx.shortest_path(_T, _first_hop, _last_hop)

           # for every switch on the path, add the MAC:PORT entry
           print "Update the path:"
           for i in range(0, len(_path)-1):
              _src = _path[i]
              _neighbor = _path[i+1]
              _portid = _T.edge[_src][_neighbor][_src]
	      # provide the port in the answer for the requester (in order to
	      # be the last getting the information
              if i == 0:
                  _host["local_port"] = _portid
              # push the MAC:PORT on the other switches on the path
              else:
                  try:
                      _url = "%s/commands" % (str(G.node[_src]["API"]))
                      _cmd = "table_add mac_table set_out_port %s => %d" % (_mac, _portid)
                      _body = {"thrift_port": G.node[_src]["thrift_port"], "commands":[_cmd]}
                      print "\tSend %s to _url %s" % (json.dumps(_body), _url)
                      response = requests.post(_url, data = json.dumps(_body), headers={"Content-Type": "application/json"})
                  except Exception as e:
                      print "Error with southbound", e
           self.finish(json.dumps(_host))
        # if unknown return an error
        else:
           self.set_status(204)
           self.finish()

# launch server
rest_app = tornado.web.Application([
           ("/host", RESTRequestHandlerHost, dict(hosts=hosts)),
           ("/host/(.*)", RESTRequestHandlerHost, dict(hosts=hosts)),
           ("/optimal", RESTRequestHandlerOptimization, dict(hosts=hosts)),
           ("/link", RESTRequestHandlerLink)
           ])
rest_server = tornado.httpserver.HTTPServer(rest_app)
rest_server.listen(PORT)
tornado.ioloop.IOLoop.current().start()
