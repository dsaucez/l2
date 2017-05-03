#!/bin/sh
while [ 1 -eq 1 ]
do
	ip=`ip -4 -o addr show eth0 | awk '{print $4}' | sed -e "s/\/.*//"`
        if [ -z $ip ]
        then
		echo "No IP found" >&2
        else
		arping -q -c 1 $ip
        fi
        sleep 10
done
