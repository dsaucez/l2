#!/bin/bash
python myController.py &
controller=$!
sudo ./cleanup2.sh && sudo ./run_demo2.sh
sudo killall cplane.py
kill $!
