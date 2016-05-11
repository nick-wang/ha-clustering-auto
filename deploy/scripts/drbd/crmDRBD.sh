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

  #Disable stonith, in case error happened, one always fence the other
  crm configure property stonith-enabled="false"

  for resname in `drbdadm dump all |grep -P "^resource .+ {" | cut -d " " -f 2`
  do
    crm configure primitive res-${resname} ocf:linbit:drbd \
                  params drbd_resource=${resname}
    crm configure ms ms_${resname} res-${resname} \
                  meta master-max=1 master-node-max=1 \
                  meta clone-max=2 clone-node-max=1 \
                  meta notify=true target-role=Started
  done
  echo "After configuring CRM"
  logit crm configure show
fi
