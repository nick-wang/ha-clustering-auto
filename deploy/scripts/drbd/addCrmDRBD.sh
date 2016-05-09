#!/bin/bash

#Configure crm resources
#Echo should configure crm resources
echo "Before configuring CRM"
logit crm configure show
for resname in `drbdadm dump all |grep -P "^resource .+ {" | cut -d " " -f 2`
do
  crm configure primitive res-${resname} ocf:linbit:drbd \
                params drbd_resource=${resname}
done
logit crm configure show
echo "After configuring CRM"

sleep 5
echo "reboot"
reboot
