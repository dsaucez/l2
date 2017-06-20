#!/usr/bin/python
# General
from scapy.all import *
import subprocess
from subprocess import Popen, PIPE
import os
import time
import random
import sys
import json


# REST API
import tornado.httpserver
import tornado.ioloop
import tornado.web
import threading
import requests

# Project
from flow import Flow
from port import Port
import lldp
import cpu
import command

# == config ====================

# == sanity checks
if len(sys.argv) != 2:
   print "usage %s <configuration file>" % (sys.argv[0])
   exit(-1)
# ===================
# cannonical name of the switch
switch_name = None

# thrift IP address for CLI
thrift_ip = None

# thrift port for CLI
thrift_port = None

# API
API = None

# CPU interface
cpu_iface = None

# ip_dic[<IP address>] = <MAC>
ip_dic = dict()

# ports[index] = <Port>
ports = dict()

abar = 0.8
V = 1.0

flows = dict()

random.seed(10)

global Q
global last_update

def load_config(filename):
    global switch_name 
    global api_url
    global thrift_port
    global thrift_ip
    global API
    global cpu_iface
    global controller_port
    global controller_ip
    """
    Load switch configuration file from `filename`

    :param filename: configuration file name
    :type filename: string
    """
    # load configuration
    with open(filename) as data_file:
        data = json.load(data_file)
        switch_name = data["switch_name"]
        thrift_ip = data["thrift_ip"]
        thrift_port = data["thrift_port"]
        API = data["API"] 
        cpu_iface = str(data["cpu_iface"])
        controller_port = str(data["controller_port"])
        controller_ip = str(data["controller_ip"])
        for d in data["ports"]:
           port = Port(index = d["index"], name = d["name"], mac = d["mac"], ip = d["ip"], prefix = d["prefix"], edge = d["edge"])
           ports[port.index] = port
      
           ip_dic[str(port.ip)]  = str(port.mac)
    
    print "######################################################"
    print "# switch name: ", switch_name
    print "# thrift ip: ", thrift_ip
    print "# thrift port: ", thrift_port
    print "# cpu_iface: ", cpu_iface
    print "# ports" , [str(p) for p in ports]
    print "# IP Dic: ", ip_dic
    print "######################################################"
    # ==============================

def flow_size(flow):
    """
    Returns the estimated size of the `flow`.

    :param flow: flow to estimate the size of
    :type flow: Flow
    :return: flow size in float
    """
    return float(int(random.random() * 5.0))

def decision_sampling(flow):
    """
    Randomly decides if the `flow` can be installed or not.

    :param flow: flow to decide installation
    :type flow: Flow
    :return: True if the flow must be insatlled. Otherwise a False is returned.
    """
    return random.random() <= abar

def decision_sequence(flow):
    """
    Decides according to the drift-plus-penalty with epoch if the `flow` can be
    installed or not.

    In this algorithm, \bar{a} is a budget of request per epoch.

    :param flow: flow to decide installation
    :type flow: Flow
    :return: True if the flow must be insatlled. Otherwise a False is returned.
    """
    global Q	              # get virtual queue
    
    dk = flow_size(flow)      # estimated flow size
    Vdk = V * dk              # flow importance

    a = int(Q <= Vdk)         # decision of installing or not based on flow
                              # importance and virtual queue size

    # some logs for fun
    print "%.2f\t%.2f\t%d" % (Q, Vdk, a)

    Q = max(Q + float(a) - abar, 0.0) # recompute virtual queue

    return bool(a)

def decision_temporal(flow):
    """
    Decides according to the temporally approximated drift-plus-penalty if the
    `flow` can be installed or not.

    In this algorithm, \bar{a} is a budget of request per second.

    :param flow: flow to decide installation
    :type flow: Flow
    :return: True if the flow must be insatlled. Otherwise a False is returned.
    """
    global Q		      # get virtual queue
    global last_update	      # last time the virtual queue was updated


    dk = flow_size(flow)      # estimated flow size
    Vdk = V * dk              # flow importance


    a = int(Q <= Vdk)         # decision of installing or not based on flow
                              # importance and virtual queue size

    # some logs for fun
    print "%.2f\t%.2f\t%d" % (Q, Vdk, a)

    # compute delta time since last update in order to know how much abar
    # we can consume
    now = time.time()
    delta = now - last_update
    ahat = abar * delta

    Q = max(Q + float(a) - ahat, 0.0) # recompute virtual queue

    last_update = now         # remember when was the last update
    return bool(a)
 
def install(flow):
    return True
    """
    Returns wether or not the `flow` must be optimally installed

    :param flow: flow to make a decision on
    :param flow: Flow
    :return: True if the flow must be optimally installed. Otherwise a False is
             returned
    """
    return decision_sequence(flow)
  
def optimal(flow):
    """
    Returns the optimal (mac, port) tuple for the `flow`.

    :param flow: flow to compute the flow placement
    :type flow: Flow
    :return: the optimal when possible: {"commands": ["list of p4 commands to be executed on the switch"...]}
    """
    _resp = None

    # send the optimization request to the controller
    ctrl = "%s:%s" % (controller_ip, controller_port)
    response = requests.post("http://%s/optimal" % (ctrl), data = json.dumps(flow.attributes()), headers={"Content-Type": "application/json","X-switch-name":switch_name})

    # ok, the controller returns us something
    if response.status_code == 200:
       _resp = json.loads(response.text)
    else:
       raise Exception("Could not optimize %s" % flow)
    
    return _resp


def send_to_CLI(cmd, cli_ip, cli_port):
    """
    Send the command `cmd` to the CLI of the P4 switch

    :param cmd: command to be executed by the CLI
    :type cmd: string
    :param cli_ip: IP address of the CLI
    :type cli_ip: string
    :param cli_port: port number of the CLI
    :type cli_port: int
    """
    this_dir = os.path.dirname(os.path.realpath(__file__))
    args = [os.path.join(this_dir, "sswitch_CLI.sh"), str(cli_ip), str(cli_port)]
    print args, cmd
    p = Popen(args, stdout=PIPE, stdin=PIPE)
    output = p.communicate(input=cmd)[0]


def _update_mac(ip, mac, port, controller=False):
    """
    Update the cache keeping `ip`:`mac` association.

    :param ip:
    :type ip: string
    :param mac:
    :type mac: string
    :param port:
    :type port: int
    :param controller:
    :type controller: Boolean
    """
    print "Learned", ip, " with ", mac, " on ", port

    ip_dic[ip] = mac    # remember the IP:MAC

    # LEARN MAC on port
    cmd = command.macPort(mac, port)
    send_to_CLI(cmd, cli_ip=thrift_ip, cli_port=thrift_port)

    # inform the controller about this new information
    if controller:
        _host = {
            "ip":ip,
            "mac": mac,
            "switch": switch_name,
            "switch_port": port
        }
        ctrl = "%s:%s" % (controller_ip, controller_port)
        r = requests.post("http://%s/host" % (ctrl), data = json.dumps(_host), headers={"Content-Type": "application/json", "X-switch-name":switch_name})

# arp_hdr.pdst
def _get_mac(ip):
    """
    Returns the MAC address associated to `ip` on the current switch

    If the MAC is not known yet by the switch, a request is sent to the
    controller to learn it. The result is then cached locally for future
    requests.
    
    :param ip: IP address to resolv
    :type ip: string
    :return: mac address (string) for IP
    """
    # if we know a MAC address for the IP respond directly
    if ip in ip_dic.keys():
        print "known IP %s" % (ip)
        _hwsrc = ip_dic[ip]

    # otherwise ask the controller
    else:
        print "Unknown IP %s, ask the controller" % (ip)

        ctrl = "%s:%s" % (controller_ip, controller_port)
        response = requests.get("http://%s/host/%s" %(ctrl, ip), headers={"X-switch-name":switch_name})

        # ok, the controller returns us something
        if response.status_code == 200:
            _resp = json.loads(response.text)
            _hwsrc = str(_resp["mac"])         # get the MAC
            _port = _resp["forward_port"]      # get the port to use localy
            _update_mac(ip, _hwsrc, _port, controller=False) # remember the IP:MAC
        # the controller doesn't know the host
        else:
            raise Exception("unknown host %s" % (ip))

    return _hwsrc

def _process_arp_request(arp_hdr, port):
    """
    Process the ARP request `arp_hdr` received on a `port` of the switch.
 
    Learn automatically the source IP:MAC association from the ARP request.
    If no MAC is known for the requested IP, send a request to the controller.

    When a MAC is known for the requested IP, a forged ARP is-at is sent on
    `port` with sources corresponding to the requested IP instead of the
    switch!!!
    
    :param arp_hdr: ARP header from scapy
    :type arp_hdr: scapy.layers.l2.ARP
    :param port: port index on which the ARP request has been received
    :type port: int
    """
    # update the local IP:MAC cache and inform the controller about the newly
    # learned association.
    if arp_hdr.psrc not in ip_dic.keys():
        print "we don't know %s" % (arp_hdr.psrc)
        _update_mac(arp_hdr.psrc, arp_hdr.hwsrc, port, controller=True) 
    else:
        print "we already know %s" % (arp_hdr.psrc)

    # implement the ARP proxy
    # prepare an ARP response
    _iface = ports[port].name   # send the reply on the interface we receive
                                # the request

    _hwdst = arp_hdr.hwsrc      # let's forge the source MAC of the reply
    _hwsrc = None               # the MAC address we want to know

    _ipdst = arp_hdr.psrc       # let's forge the source IP of the reply
    _ipsrc = arp_hdr.pdst       # the IP address for which we want to know the
                                #MAC 

    # get the MAC address for the requested IP
    _hwsrc = _get_mac(arp_hdr.pdst)

    # If the IP:MAC association is known, send a forged ARP reply
    if _hwsrc:
       print "REPONSE (%s, %s) with (%s, %s) on %s" % (_hwsrc, _hwdst, _ipsrc, _ipdst, _iface)
       sendp( Ether(dst=_hwdst, src=_hwsrc)/ARP(op="is-at", hwsrc=_hwsrc, psrc=_ipsrc, pdst=_ipdst), iface=_iface, verbose=False)

def _process_arp_response(arp_hdr, port):
    """
    Process the ARP response `arp_hdr` received on a `port` of the switch.
    
    NOT IMPLEMENTED

    :param arp_hdr: ARP header from scapy
    :type arp_hdr: scapy.layers.l2.ARP
    :param port: port index on which the ARP response has been received
    :type port: int
    """
    pass

def process_arp(ether_hdr, port):
    """
    Process ARP message `arp_hdr` received on a `port` of the switch.

    See _process_arp_request(arp_hdr, port) for ARP requests
    See _process_arp_response(arp_hdr, port) for ARP responses

    :param arp_hdr: Ethernet header from scapy
    :type arp_hdr: scapy.layers.l2.Ether
    :param port: port index on which the ARP has been received
    :type port: int
    """
    # extract ARP header
    arp_hdr = ether_hdr['ARP']

    # ARP request
    if arp_hdr.op == 1:
       _process_arp_request(arp_hdr, port)
    # ARP response
    elif arp_hdr.op == 2:
       _process_arp_response(arp_hdr, port)
    # unsupported
    else:
       raise Exception("Unsupport ARP type")


def process_lldp(ether_hdr, port):
    """
    Process LLDP message `ether_hdr` received on a `port` of the switch.

    Notify the controller (see /link) when a new port is discovered.

    :param ether_hdr: Ethernet header from scapy
    :type ether_hdr: scapy.layers.l2.Ether
    :param port: port index on which the LLDP has been received
    :type port: int
    """

    # extract LLDP header
#    chassis_tlv = ether_hdr['Chassis ID'] 
#    port_tlv = ether_hdr['Port ID'] 
    lldp_str = ether_hdr
    chassis_tlv = lldp.Chassis_Id(lldp_str)
    port_tlv = lldp.Port_Id(lldp_str[(chassis_tlv.length+2):])
    print "learned %s:%d on port %d " % (chassis_tlv.locallyAssigned, int(port_tlv.locallyAssigned), port)

    # link parameters (see controller API /link)
    data = {
       "name":switch_name,
       "src":chassis_tlv.locallyAssigned,
       "dst":switch_name,
       chassis_tlv.locallyAssigned: int(port_tlv.locallyAssigned),
       switch_name:port,
       "API": API,
       "thrift_ip":thrift_ip,
       "thrift_port":thrift_port
    }

    # send the optimization request to the controller
    ctrl = "%s:%s" % (controller_ip, controller_port)
    response = requests.post("http://%s/link" % (ctrl), data = json.dumps(data), headers={"Content-Type": "application/json","X-switch-name":switch_name})

def process_cpu_pkt(ether_hdr):
    """
    Process packet `p` received on the slow path.
    Extract flow information from CPU packet and optimize the flow according to
    the policy

    Specfic cases:
      o See process_arp() for ARP
      o See process_lldp() for LLDP

    :param p: packet to be processed
    :type p: scapy.layers.l2.Ether
    """
    # Get info about the new flow
    cpu_hdr = None      # CPU header
    ip_hdr = None	# IP header

    # data to decide the frame treatement
    ether_type = None
    if_index = None

    # data to decide flow information (5-tuple)
    protocol = None
    srcAddr = None
    dstAddr = None
    srcPort = None
    dstPort = None
    
    # CPU
    try:
       # treat only CPU messages
       if ether_hdr.type != 0xDEAD:
         raise Exception("Not a CPU message")

       # extract CPU header
       cpu_hdr = ether_hdr['CPUHeader'] 
       if_index = cpu_hdr.ifIndex
       ether_type = cpu_hdr.etherType
       print "CPU", ether_type
    except Exception as e:
       print "Error extracting CPU", e
       return

    # ARP
    if ether_type == 0x0806:
       try:
          process_arp(ether_hdr, if_index)
          print "\tARP"
          return
       except Exception as e:
          print "Error extracting ARP", e
          return
    # LLDP
    elif ether_type == 0x88cc:
       try:
          p_str = str(ether_hdr)
          p_str2 = p_str[:12] + p_str[24:26] + p_str[26:]
          process_lldp(p_str2[14:], if_index)
#          process_lldp(ether_hdr, if_index)
          print "LLDP"
          return
       except Exception as e:
          print "Error extracting LLDP", e
          return
    # IP
    elif ether_type == 0x0800:
       try:
          ip_hdr = ether_hdr['IP']
          protocol = ip_hdr.proto
          srcAddr = ip_hdr.src
          dstAddr = ip_hdr.dst
          print "\tIP"
       except Exception as e:
          print "Error extracting IP", e
          return
    # not supported
    else:
       print "Unsupported protocol"
       return

    # Assign default src/dst ports if ICMP
    if protocol == 1:
      try:
          icmp_hdr = ip_hdr['ICMP']
          srcPort = 0
          dstPort = 0
          print "\t\tICMP"
      except Exception as e:
          print "Error extracting ICMP", e
          return
    # try to get TCP information
    elif protocol == 6: 
       try:
          tcp_hdr = ip_hdr['TCP']
          srcPort = tcp_hdr.sport
          dstPort = tcp_hdr.dport
          print "\t\tTCP"
       except Exception as e:
          print "Error extracting TCP",e
          return
    # try to get UDP information
    elif protocol == 17: 
       try:
          udp_hdr = ip_hdr['UDP']
          srcPort = udp_hdr.sport
          dstPort = udp_hdr.dport
          print "\t\tUDP"
       except Exception as e:
          print "Error extracting UDP",e
          return
    else:
       print "Unsupported protocol"
       return

    # Build flow information
    flow = Flow(srcAddr, dstAddr, protocol, srcPort, dstPort)
    key = str(flow)


    # Check if we have to do something
    # process only if coming from an edge port
    if not ports[if_index].edge:
       print "Optimization of flow %s ignored as not received on edge port " % (switch_name)
       return
    # do not process flows if a request for processing has been sent recently
    now = time.time()
    if key in flows.keys():
       if flows[key] > (now - 5.): # no more than one request every 5 sec for the flow
           print "Flow %s has been requested recently" % (key)
           return 
       else:
           print "                                We know the flow ", (key)
    flows[key] = now


    # install a flow table entry in the switch
    try:
       cmds = list()
       # if it can installed, optimize it
       if install(flow):
         # get optimal placement
         opt = optimal(flow)
         cmds = opt["commands"]
       # if it cannot be installed, follow the default path
       else:
         cmd = command.flowIgnore(flow)
         cmds.append(cmd)

       # exectude all the commands
       for cmd in cmds:
           send_to_CLI(cmd, cli_ip=thrift_ip, cli_port=thrift_port)
    except Exception as e:
       print e 

# == South bound interface ==================================
class RESTRequestHandlerCmds(tornado.web.RequestHandler):
    # POST /host
    def post(self):
        results = list();
        self.set_header("Content-Type", 'application/json; charset="utf-8"')
        params = json.loads(self.request.body.decode())
        print "Execute commands: ", str(params["commands"])
        for cmd in params["commands"]:
           r = send_to_CLI(cmd, cli_ip=params["thrift_ip"], cli_port=params["thrift_port"])
           results.append((cmd, r))
        self.set_status(201)
        self.finish(json.dumps({"output":results}))

def south_bound():
    """
    Launch the south-bound REST API

    Listens on port defined by `API` configuration attribute
    """
    # map API to handlers
    rest_app = tornado.web.Application([
           ("/commands", RESTRequestHandlerCmds)
           ])
    rest_server = tornado.httpserver.HTTPServer(rest_app)
    
    # get the port to listen on
    lport = int(API.split(":")[-1])   

    # start the server
    rest_server.listen(lport)
    tornado.ioloop.IOLoop.current().start()
# ============================================================

def slow_path():
    """
    Listens for packets on CPU interface
    
    see process_cpu_pkt()
    """
    print "#Q\tV*dk\ta"
    sniff(iface=cpu_iface, prn=lambda x: process_cpu_pkt(x))

if __name__ == '__main__':
    global Q
    global last_update

    load_config(sys.argv[1])
 
    # Scapy bindings
    bind_layers(Ether, cpu.CPUHeader, type=0xDEAD)
    bind_layers(cpu.CPUHeader, ARP, etherType=0x0806)
    bind_layers(cpu.CPUHeader, lldp.Chassis_Id, etherType=0x88cc)
    bind_layers(cpu.CPUHeader, IP, etherType=0x0800)
    bind_layers(lldp.Chassis_Id, lldp.Port_Id)
    bind_layers(lldp.Port_Id, lldp.TTL)

    # virtual queue
    last_update = time.time()
    Q = 0.0

    # Launch southbound interface 
    t = threading.Thread(target=south_bound)
    t.start()

    # Listen slow-path events
    slow_path()
