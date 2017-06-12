# SDN forwarding and switching - routing and optimization

With the advent of Software Defined Networking (SDN) comes great freedom in the
way you manage your network. However, it also comes with two great questions:

1. How and when to propagate forwarding information in the network?
2. How to compute routes?

Due to the short time of the lab session and to focus on the concepts, the lab
will be realised on a simple home-made SDN controller written in Python that
abstracts the technology used to implement SDN. 

## Background

### Forwarding information diffusion

Most of the time with SDN the control plane and the data plane are completely
separated meaning that information between them have to be propagated using
specific mechanisms.

We can distinguish two main options to diffuse forwarding information.

1. _Push_: The controller sends the forwarding information to the switch
without any request issued by the switch.

2. _Pull_: The switch sends a request with packet information to the controller
that triggers this latter to send back a response with the forwarding
information.

In practice, it is usually possible to combine the _push_ and the _pull_
mechanism to take the most of each technique. In the remaining of this course,
we will call it _pull-push_. In this lab, we will use this approach.

#### Pull-push in this lab

We implement _pull-push_ as follows: when an ingress switch receives a packet
that does not match any entry of its forwarding table, it triggers a request to
the controller via its REST API to indicate that it just experienced a miss.
The controller will then decide on the fly the route for the packet and reply
to the switch with the forwarding action to perform. If multiple switches are
on the path to the destination, the controller will _push_ the forwarding
information to the subsequent switches on the path so that they don't trigger
miss.

In the _pull-push_ case, it is essential, particularly at layer 2 that cannot
prevent frame loops, to ensure that routes are correctly pushed on the switches
before forwarding packets otherwise transient loop may occur or unnecessary
control plane message may be sent. In this lab, we will install routes from the
the first hop to the last hop sequentially and then only to the switch that
triggers the request. That way, a packet will not be forwarded on the path as
long as it is not set up entirely.

### Flow 

Packets carry plethora of information, such as source of destination MAC
address, destination IP address, L4 port numbers... A _flow_ is an equivalence
class linking packets of the same communication. The equivalence is defined by
the information contained in the various packet headers.

The main type of flows used in routing are the following.

o *Layer 2 destination*: all frames for the same L2 destination (i.e.,
destination MAC address).

o *Layer 3 destination*: all packets for the same L2 destanation (i.e.,
destination IP prefix or destination IP address).

o *5-tuples*: all packets with the same source and destination IP addresses, L4
protocol, and L4 source and destination ports.

### Routing policies

It is common to follow shortest path routing and prefix-based matching but with
SDN we can implement any type of routing policy. The aim of this lab is not to
study the various possible routing policies but instead to see that the choice
of a policy may impact the performance one can obtain and also that the
forwarding information diffusion technique has an impact of what policy can
actually be implemented.

Below we describe the two most common routing policies.

#### Minimum spanning tree routing

A spanning tree _T=(V,E')_ of an undirected graph _G = (V,E)_ is a connected
undirected tree that includes all the vertices of _G_ such that _E'_ is a
subset of _E_.  A spanning tree is minimum if the the sum of the weight of its
edges (i.e., _E'_) is minimum given _G=(V,E)_.

Routing on the minimum spanning tree is done by forwarding packets between two
nodes (i.e., vertices) along the minimum spanning tree.

#### Shortest path routing

A path _p(a,b)_ between two edges _a_ and _b_ in a graph _G=(V,E)_ is the
shortest if there is no path _p'(a,b)_ in _G_ where the sume of the weight of
its edges is lower than the one of _p_.

Routing on the shortest path between two edges is done by forwarding packets
between these edges along the shortest path.

##### Load balancing

When multiple spanning trees or shortest paths exist, load balancing is often
performed meaning that the traffic can be spread on all the paths to the
destination.

Different solutions exist to perform load balancing. The two most common
solution are: 

1. Random: the shortest path to be followed by a packet is selected randomly,
for each packet.

2. Deterministic: the shortest path to be followed by a packet is selected
according to a deterministic function, for each packet. To guarantee stability
of packets of a given flow, the function usually returns the same choice for
every packet belonging to the same flow.

## Lab instructions

In this lab you will deploy the following topology with
[Mininet](http://mininet.org).

![alt text](topo.png "Network topology")

Switches are implemented with [P4](http://p4.org) and the SDN controller is
implemented in Python just for the sake of this lab.

During the lab session you will first implement shortest path routing for
*Layer 3 destination* and *5-tuples* flows. You will then implement a mechanism
to balance the load based on the infromation given by the *5-tuples* flows.

Every time a switch receives a packet for which it doesn't know the forwarding
port, the controller receives a _pull_ request. You will implement the
algorithm that computes the path to follow for this packets according to your
routing policy. Once the path is known, you will reply to the requesting switch
with the port to use (i.e., reply to the _pull_) and _push_ the decision on the
other switches on ther way to the destination. This way corresponds to
implementing the _pull-push_ method.

### Implementation

#### Prepare your environement

Start your lab virtual machine and log into it (_user/user_).

The lab material is installed in `LAB4` directory. Go in this directory and
download the latest code needed for the lab:

```bash
$ cd ~/LAB4/tutorials/examples
$ git clone https://github.com/dsaucez/l2.git
$ cd l2
```

#### Time to code!

The Python program you have to modify is called `myController.py`, located in
`~/LAB4/tutorials/examples/l2`.

More specifically, you have to implement the `getPath(src, dst, flow)` method
that returns the path to be used between switches `src` and `dst` for a flow.

To compute the path, the variable `self.topology.G` is a graph representation
of the topology as learned by the controller. The type of this variable is
`networkx.classes.graph.Graph`, have a look at
[[1]](https://networkx.github.io/documentation/networkx-1.10/reference/algorithms.shortest_paths.html)
and
[[2]](https://networkx.github.io/documentation/networkx-1.10/reference/algorithms.mst.html)
to see various useful graph algorithms proposed by the NetworkX library.

Have a look at the method `_routing(switch, flow)` to see how the _pull-push_
method is implemented in the controller.


##### Question 1

Modify `getPath(src, dst, flow)` to implement *Layer 3 destination based
shortest path routing*.

Describe your algorithm and implement it.

##### Question 2

Modify `getPath(src, dst, flow)` to implement *5-tuples shortest path routing*.

Describe your algorithm and implement it.

##### Question 3

Modify your implementation of Question 2 to support load balancing.

a) Describe an algorithm for random load balancing oblivious to network load
and implement it.

b) Describe an algorithm for deterministic load balancing oblivious to network
load and implement it.

c) Would it be useful to implement a load balancing technique that accounts for
the actual load of the network?

   c.i) Does it imply extra communication between the switches and the
controller?

   c.ii) What are the benefits of accounting for the actual load of the network?
   
   c.iii) What are the drawbacks of accounting for the actual load of the network?

##### Question 4

In the lab we worked only with the _pull-push_ method. What are the advantages
of _push_, _pull_, and _pull-push_ methods, respectively?

### Testing your code

We use Mininet to emulate the topology. To test your implementation, open a new
terminal and run the following commands to start mininet.

```bash
$ cd ~/LAB4/tutorials/examples/l2
$ ./start_mininet
```

This has for effect to start your controller and to lauchn Mininet with the
topology presented in the figure above. Starting the environement may take some
time, once you see the message `READY: topology discovered!` it means your
controller discovered the entire topology and you are ready to accept traffic
between hosts.


##### Question 5

During the week you (re)discovered the cloud. Based on what you have learned,
implement a small application that will allow you to test the different
implementations you did in Question 1, 2, and 3.

Some examples of commands that you may used to implement your application with
Mininet:

```
mininet> h11 dd if=/dev/urandom of=BIG count=10 bs=10M
mininet> h21 python -m SimpleHTTPServer 80 &
mininet> h11 wget http://192.0.2.21/BIG > /dev/null
mininet> pingall
mininet> iperf h11 h22
```


##### Bonus question

What are the respective advantages of the _push_, _pull_, and _pull-push_
methods?


