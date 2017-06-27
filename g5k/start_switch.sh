# prepare CPU interface
echo "Preparing CPU interface..."
intf0="cpu-veth-0"
intf1="cpu-veth-1"
if ! ip link show $intf0 &> /dev/null; then
    ip link add name $intf0 type veth peer name $intf1
    ip link set dev $intf0 up
    ip link set dev $intf1 up
fi
sysctl net.ipv6.conf.$intf0.disable_ipv6=1
sysctl net.ipv6.conf.$intf1.disable_ipv6=1

# compile P4
echo "Compile fast path..."
p4c-bmv2 ../p4src/l2.p4 --json l2.json || exit

# start fast path
echo "Starting fast path"
nohup simple_switch -i 1@if1 -i 2@if2 -i 11@cpu-veth-1 l2.json &

# start slow path
sleep 30
echo "Starting slow path..."
nohup ../cplane.py config/s10.json &

# configure fast path
sleep 30
echo "Configuring fast path..."
simple_switch_CLI --thrift-ip 127.0.0.1 < ../commands2.txt 
