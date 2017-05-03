
Start the router:

$ sudo ./cleanup.sh
$ sudo ./run_demo.sh 


Start the controller:

$ sudo ./cplane.py

Generate traffic:

mininet> H1 echo "coucou" | nc H2 80
