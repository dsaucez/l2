# Start the network:

```bash
$ sudo ./cleanup2.sh && sudo ./run_demo2.sh
```

# Start the controller:
```bash
$ python myController.py
```

# Start the control plane demons:

```bash
$ sudo sh switches.sh
```

# Generate some traffic:

```bash
mininet> pingall
```
