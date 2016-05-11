#!/bin/bash

#Import ENV conf
. cluster_conf
. scripts/functions
. scripts/drbd/drbd_functions

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
                  params drbd_resource=${resname} \
                  op start timeout=240 \
                  op stop timeout=100
    crm configure ms ms_${resname} res-${resname} \
                  meta master-max=1 master-node-max=1 \
                  meta clone-max=2 clone-node-max=1 \
                  meta notify=true target-role=Started
    if [ ${NODES} -gt 2 ]
    then
      i=3
      while [ ${i} -le ${NODES} ]
      do
        temp=HOSTNAME_NODE${i}
        crm configure location l-${resname}-${i} ms_${resname} \
                      -inf: $(eval echo \$${temp})
        i=$((i+1))
      done
    fi
  done

  echo "After configuring CRM"
  logit crm configure show
fi
logit crm_mon -1

case $(getDRBDVer) in
  9)
    logit drbdadm status all
    ;;
  84)
    logit cat /proc/drbd
    ;;
  *)
    echo "Error! Wrong DRBD version."
esac
