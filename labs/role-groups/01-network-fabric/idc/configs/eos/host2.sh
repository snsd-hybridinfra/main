#!/bin/sh
set -eu
nic=$1
ip link set dev "$nic" up
ip link add link "$nic" name idc-v10 type vlan id 10
ip addr add 198.51.100.12/26 dev idc-v10
ip link set dev idc-v10 up
ip link add link "$nic" name idc-v30 type vlan id 30
ip addr add 198.51.100.135/26 dev idc-v30
ip link set dev idc-v30 up
ip route add 198.51.100.64/26 via 198.51.100.129 dev idc-v30
