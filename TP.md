# SDN forwarding and switching - routing and optimization

With the advent of Software Defined Networking (SDN) comes great freedom in the
way you manage your network. However, it also comes with two great questions:

1. How and when to propagate forwarding information in the network?
2. How to compute routes?

In this hands-on lab, we will explore these two points by first implementing a
reactive and a proactive forwarding information diffusion mechanism. Then we
will implement various routing policies.

To understand the impact of each solution, we will compare them with the same
benchmark distributed application and discover that depending on the scenario
the performance of the application relying on the network may be really
different.

Due to the short time of the lab session and to focus on the concepts, the lab
will be realised on a simple home-made SDN controller written in Python that
abstracts the technology used to implement SDN. We will propose for the
hackathon to implement these concepts in ONOS.

## Context and terminology

### Forwarding information diffusion

Most of the time with SDN the control plane and the data plane are completely
separated meaning that information between them have to be propagated using
specific mechanisms.

We can distinguish two main options to diffuse forwarding information.

1. Push: The controller sends the forwarding information to the switch without
any request issued by the switch.

2. Pull: The switch sends a request with packet information to the controller
that triggers this latter to send back a response with the forwarding
information.

The main advantage with the _push_ mechanism is that no delay is added because
of waiting for the policies made by the controller. The main drawback is that
it is not possible to implement fine grain policies.

On the contrary, the _pull_ options allows one to implement arbitrarily precise
policies (potentially a different policy for every packet) but it comes at
the cost of addition delay and potentially high load on the controller.

In practice, it is usually possible to combine the _push_ and the _pull_
mechanism to take the most of each technique. In the remaining of this course,
we will call it _pull-push_.

#### Push

We will implement _push_ as follows: every time the controller detects a change
in the topology, it will recompute the routes and update the switches via their
REST API to reflect the new routes in their forwarding table.

#### Pull

We will implement _pull_ as follows: when a switch receives a packet that does
not match any entry of its forwarding table, it triggers a request to the
controller via its REST API to indicate that it just experienced a miss. The
controller will then decide on the fly the route for the packet and reply to
the switch with the forwarding action to perform.

#### Pull-push

We will implement _pull-push_ as follows: when an ingress switch receives a
packet that does not match any entry of its forwarding table, it triggers a
request to the controller via its REST API to indicate that it just experienced
a miss. The controller will then decide on the fly the route for the packet and
reply to the switch with the forwarding action to perform. If multiple switches
are on the path to the destination, the controller will _push_ the forwarding
information to the subsequent switches on the path so that they don't trigger
miss.

In the _pull-push_ case, it is essential, particularly at layer 2, to ensure
that routes are correctly pushed on the switches before forwarding packets
otherwise transient loop may occur or unnecessary control plane message may be
sent. In this lab, we will install routes from the last hop to the first hop
sequentially.

### Routing policies

While it is common to follow shortest path routing and prefix-based matching,
with SDN we can implement any type of routing policy. The aim of this lab is
not to study the various possible routing policies but instead to see that the
choice of a policy may dramatically impact the performance one can obtain and
also that the forwarding information diffusion technique has an impact of what
policy can actually be implemented.

In this lab, we will consider the following 4 routing policies.

#### Minimum spanning tree

A spanning tree _T=(V,E')_ of an undirected graph _G = (V,E)_ is a connected
undirected tree that includes all the vertices of _G_ such that _E'_ is a
subset of _E_.  A spanning tree is minimum if the the sum of the weight of its
edges (i.e., _E'_) is minimum given _G=(V,E)_.

Routing on the minimum spanning tree is done by first computing a minimum
spanning tree of the network. Packets between two nodes (i.e., vertices) are
forwarded along the shortest of these paths.

#### L2 destination based shortest path routing

Layer 2 destination based shortest path routing consists in forwarding Ethernet
frames to a destination by following one of the shortest paths to that
destination.

#### L3 destination based shortest path routing

Layer 3 destination based shortest path routing consists in forwarding IP
packets to a destination by following one of the shortest paths to that
destination.

#### L4 flow based shortest path routing with load balancing

Layer 4 flow based shortest path routing consists in forwarding all packets
belonging to the same layer 4 flow by following one of the shortest paths
between the source and the destination of the packet. When multiple such paths
exist, one can do load balancing meaning that the traffic can be spread on all
the paths to the destination.

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

During the lab session you will implement the *L3 destination based shortest
path routing* and the *L4 flow based shortest path routing with load balancing*
in _pull-push_ mode.

Every time a switch receives a packet for which it doesn't know the forwarding
port, the controller receives a pull request. You will implement the algorithm
that computes the path to follow for this packets according to your routing
policy. Once the path is known, you will reply to the requesting switch with
the port to use (i.e., reply to the _pull_) and push the decision on the other
switches on ther way to the destination.

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
[1](https://networkx.github.io/documentation/networkx-1.10/reference/algorithms.shortest_paths.html)
and
[2](https://networkx.github.io/documentation/networkx-1.10/reference/algorithms.mst.html)
to see various useful graph algorithms proposed by the NetworkX library.

Have a look at the method `_routing(switch, flow)` to see how the _pull-push_
method is implemented in the controller.

##### Question 1

Modify `getPath(src, dst, flow)` to implement *L3 destination based shortest
path routing*.

a) Describe your algorithm and implement it.

b) Why is getPath(src, dst, flow) called for every new 5-tuple flow while you
implemented a L3 destination based shortest path routing? Hint: see method
`_routing(self, switch, flow)` and file `p4src/l2.p4`.

c) In presence of multiple equal shortest path, how do you decide to chose a
particular one?

##### Question 2

Modify `getPath(src, dst, flow)` to implement *L4 flow based shortest path
routing with load balancing*.

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

### Testing your code
We will now start Mininet to emulate the topology, for that, open a new
terminal

#### 
```bash
$ cd ~/LAB4/tutorials/examples/l2
$ ./start_mininet
```

This has for effect to start mutliple instances of the 

#### Terminal 2
```bash
$ cd LAB4/tutorials/examples/l2
$ ./start_controller
```

### Terminal 3
```
$ cd LAB4/tutorials/examples/l2
$ ./start_switches
```



