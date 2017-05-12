# prepare CPU interface
sh interfaces.sh
# compile P4
p4c-bmv2 p4src/counter.p4 --json counter.json
# start switch
simple_switch --log-console -i 1@if11 -i 2@if12 -i 11@cpu-veth-1 --thrift-port 45010 counter.json
