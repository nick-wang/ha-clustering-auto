#!/bin/bash

#Import ENV conf
. cluster_conf
. scripts/functions

#config stonith resource on node1
isMaster "$HOSTNAME_NODE1"
if [ $? -eq 0 ]
then
    if [ $STONITH == "sbd" ];
    then
        crm configure primitive sbd_stonith stonith:external/sbd
    else
        crm configure primitive libvirt_stonith stonith:external/libvirt \
                  params hostlist="$NODE_LIST" \
                  hypervisor_uri="qemu+tcp://$HOST_IPADDR/system" \
                  op monitor interval="60"
    fi
    infoRun crm configure show

fi
