#!/bin/bash

THIS_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

source $THIS_DIR/../../env.sh

CLI_PATH=$BMV2_PATH/targets/simple_switch/simple_switch_CLI
TOOL_PATH=$BMV2_PATH/tools/
echo $TOOL_PATH

PYTHONPATH=$PYTHONPATH:$TOOL_PATH python $CLI_PATH --thrift-ip $1 --thrift-port $2
