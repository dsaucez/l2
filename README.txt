
Start the network:
$ sudo ./cleanup2.sh && sudo ./run_demo2.sh


Start the controller:
$ python controller.py

Start the south bound interface:
$ python south_bound.py 8080

Start the control plane demons:
$ sudo sh switches.sh

Generate some traffic:
mininet> pingall
