#!/bin/bash

function usage()
{
  echo "$0 <NIC>"
}

if [ $# -gt 1 ];then
  usage
  exit -1
fi

if [ x"$1" != x"" ];then
  NIC=$1
else
  NIC="eth0"
fi

IPMASK=$(ip a show dev ${NIC}|grep "inet "|xargs|cut -d " " -f 2)

if [ -z ${IPMASK} ];then
  echo "Won't replace dhcp to static, since no IP found in ${NIC}"
  exit -2
fi

# dhcp example /etc/sysconfig/network/ifcfg-eth0
# NAME=''
# BOOTPROTO='dhcp'
# STARTMODE='auto'
# ZONE=''

# static example /etc/sysconfig/network/ifcfg-eth0
# IPADDR='10.67.17.113/21'
# BOOTPROTO='static'
# STARTMODE='auto'

echo "Force convert IP retrieve from dhcp to static: $IPMASK"

cp /etc/sysconfig/network/ifcfg-${NIC} /etc/sysconfig/network/ifcfg-${NIC}.bak

cat <<EOF >> /etc/sysconfig/network/ifcfg-${NIC}
IPADDR='${IPMASK}'
BOOTPROTO='static'
STARTMODE='auto'
EOF
