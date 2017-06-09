# prepare CPU interface
./interfaces.sh
# compile P4
p4c-bmv2 ../p4src/l2.p4 --json l2.json
# start switch
simple_switch --log-console -i 1@if11 -i 2@if12 -i 11@cpu-veth-1 --thrift-port 45010 l2.json
