#!/bin/bash
if [ ! -d log ] 
then
   mkdir log
fi
if [ ! -d config ]
then
   mkdir config
fi

python myController.py &
controller=$!
sudo ./cleanup2.sh && sudo ./run_demo2.sh
sudo killall cplane.py
kill $!
