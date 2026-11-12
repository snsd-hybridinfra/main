#!/bin/sh
set -eu
nic=$1
ip link set dev "$nic" up
ip link add link "$nic" name idc-v10 type vlan id 10
ip addr add 198.51.100.11/26 dev idc-v10
ip link set dev idc-v10 up
ip link add link "$nic" name idc-v20 type vlan id 20
ip addr add 198.51.100.71/26 dev idc-v20
ip link set dev idc-v20 up
ip route add 198.51.100.128/26 via 198.51.100.65 dev idc-v20
