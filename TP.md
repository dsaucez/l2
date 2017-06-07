# SDN forwarding and switching - routing and optimization

With the advent of Software Defined Networking (SDN) comes great freedom in the
way you manage your network. However, it also comes with two great questions:

1. How and when to propagate forwarding information in the network?
2. How to compute routes?

In this hands-on lab, we will explore these two points by first implementing a
reactive and a proactive forwarding information diffusion mechanism. Then we
will implement various routing decisions.

To understand the impact of each solution, we will compare them with the same
benchmark distributed application and discover that depending on the scenario
the performance of the application relying on the network may be really
different.

Due to the short time of the lab session and to focus on the concepts, the lab
will be realised on a simple home-made SDN controller written in Python that
abstracts the technology used to implement SDN. We will propose for the
hackathon to implement these concepts in ONOS.


## Forwarding information diffusion

Most of the time with SDN the control plane and the data plane are completely
separated meaning that information between them have to be propagated using
specific mechanisms.

We can distinguish two main options to diffuse forwarding information.

1. Push: The controller sends the forwarding information to the switch without
any request issued by the switch.

2. Pull: The switch sends a request with packet information to the controller
that triggers this latter to send back a response with the forwarding
information.

The main advantage with the `push` mechanism is that no delay is added because
of waiting for the decision made by the controller. The main drawback is that
it is not possible to implement fine grain policies.

On the contrary, the `pull` options allows one to implement arbitrarily precise
policies (potentially a different decision for every packet) but it comes at
the cost of addition delay and potentially high load on the controller.

In practice, it is usually possible to combine the `push` and the `pull`
mechanism to take the most of each technique. In the remaining of this course,
we will call it `pull-push`.

#### Push

We will implement `push` as follows: everytime the controller detects a change
in the topology, it will recompute the routes and update the switches via their
REST API to reflect the new routes in their forwarding table.

#### Pull

We will implement `pull` as follows: when a switch receives a packets that does
not match any entry of its forwarding table, it triggers a request to the
controller via its REST API to indicate that it just experienced a miss. The
controller will then decide on the fly the routes for the packet and reply to
the switch with the forwarding action to perform.

#### Pull-push

We will implement `pull-push` as follows: when an ingress switch receives a
packets that does not match any entry of its forwarding table, it triggers a
request to the controller via its REST API to indicate that it just experienced
a miss. The controller will then decide on the fly the routes for the packet
and reply to the switch with the forwarding action to perform. If multiple
switches are on the path to the destination, the controller will `push` the
forwarding information to the subsequent switches on the path.

## Routing decisions

While it is common to follow shortest path routing and prefix-based matching,
with SDN we can 






















