#!/bin/bash

# Copyright 2013-present Barefoot Networks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

if [[ $EUID -ne 0 ]]; then
    echo "This script should be run using sudo or as the root user"
    exit 1
fi

THIS_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

source $THIS_DIR/../../../env.sh

P4C_BM_SCRIPT=$P4C_BM_PATH/p4c_bm/__main__.py

SWITCH_PATH=$BMV2_PATH/targets/simple_switch/simple_switch

CLI_PATH=$BMV2_PATH/targets/simple_switch/sswitch_CLI

# create CPU ports
for s in "s11" "s12" "s13" "s14" "s21" "s22" "s23" "s24"
do
  intf0="cpu-veth-0$s"
  intf1="cpu-veth-$s"
  if ! ip link show $intf0 &> /dev/null; then
      ip link add name $intf0 type veth peer name $intf1
      ip link set dev $intf0 up
      ip link set dev $intf1 up
#      ifconfig $intf1 1.10.1.10/32
#      ifconfig $intf1 hw ether 52:c5:69:b4:3f:c9
#      ifconfig $intf0 1.11.1.11/32
#      ifconfig $intf0 hw ether 52:c5:69:b4:3f:c8
      TOE_OPTIONS="rx tx sg tso ufo gso gro lro rxvlan txvlan rxhash"
      for TOE_OPTION in $TOE_OPTIONS; do
          /sbin/ethtool --offload $intf0 "$TOE_OPTION" off
          /sbin/ethtool --offload $intf1 "$TOE_OPTION" off
      done
  fi
  sysctl net.ipv6.conf.$intf0.disable_ipv6=1
  sysctl net.ipv6.conf.$intf1.disable_ipv6=1
done
########
$P4C_BM_SCRIPT ../p4src/l2.p4 --json l2.json
if [ $? -ne 0 ]; then
  echo "Ooops"
  exit
fi
# This gives libtool the opportunity to "warm-up"
$SWITCH_PATH >/dev/null 2>&1
PYTHONPATH=$PYTHONPATH:$BMV2_PATH/mininet/ python topo.py \
    --behavioral-exe $SWITCH_PATH \
    --json l2.json \
    --cli $CLI_PATH \
    --thrift-port 45001
