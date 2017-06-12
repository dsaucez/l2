#!/bin/bash
mkdir log
for f in config/s*.json
do
   s=`echo $f | sed -e "s/config\///" | sed -e "s/\.json//"`
   echo "Start $s"
   ./cplane.py $f > log/$s.log &
done
