#!/bin/bash

ADD_IP="true"
CI_HOST="ci.ha.suse.asia" # dns ci.ha.suse.asia -> 10.67.160.200

nslookup ${CI_HOST} > /dev/null
if [ $? -eq 0 ] && [ x"${ADD_IP}" == x"true" ];then
    HOST_IP=${CI_HOST}
else
    HOST_IP=$(ip -4 route get 8.8.8.8 | awk {'print $7'} | tr -d '\n')
fi
echo "HOST_IP: $HOST_IP"

# Need to run in this parenet folder
echo "HOST_IP=$HOST_IP" > data/HOSTENV
