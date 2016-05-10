#!/bin/bash

#Import ENV conf
. cluster_conf
. scripts/functions

#Configure crm resources
#Echo should configure crm resources
isMaster "$HOSTNAME_NODE1"
if [ $? -eq 0 ]
then
  echo "Before configuring CRM"
  logit crm configure show
  for resname in `drbdadm dump all |grep -P "^resource .+ {" | cut -d " " -f 2`
  do
    crm configure primitive res-${resname} ocf:linbit:drbd \
                  params drbd_resource=${resname}
  done
  logit crm configure show
  echo "After configuring CRM"
fi
logit crm_mon -1
  
sleep 5
echo "reboot"
