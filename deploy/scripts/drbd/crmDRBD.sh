#!/bin/bash

#Import ENV conf
. cluster_conf
. scripts/functions
. scripts/drbd/drbd_functions

nextPhase "Launch $0"

#Configure crm resources
#Echo should configure crm resources
isMaster "$HOSTNAME_NODE1"
if [ $? -eq 0 ]
then
  nextPhase "Before configuring DRBD" | tee -a ${DRBD_LOGFILE}
  logit crm configure show | tee -a ${DRBD_LOGFILE}

  #Disable stonith, in case error happened, one always fence the other
  crm configure property stonith-enabled="false"

  tempfile=drbd-tempfile
  for resname in `drbdadm dump all |grep -P "^resource .+ {" | cut -d " " -f 2`
  do
    echo "configure
          primitive res-${resname} ocf:linbit:drbd \
                    params drbd_resource=${resname} \
                    op start timeout=240 \
                    op stop timeout=100
          ms ms_${resname} res-${resname} \
             meta master-max=1 master-node-max=1 \
             meta clone-max=2 clone-node-max=1 \
             meta notify=true target-role=Started" > $tempfile
    if [ ${NODES} -gt 2 ]
    then
      i=3
      while [ ${i} -le ${NODES} ]
      do
        temp=HOSTNAME_NODE${i}
        echo "
        location l-${resname}-${i} ms_${resname} \
                      -inf: $(eval echo \$${temp})" >>$tempfile
        i=$((i+1))
      done
    fi
    crm -f ${tempfile}
  done

  nextPhase "After configuring DRBD" | tee -a ${DRBD_LOGFILE}
  logit crm configure show | tee -a ${DRBD_LOGFILE}
fi
sleep 3

logit crm_mon -1 | tee -a ${DRBD_LOGFILE}
case $(getDRBDVer) in
  9)
    logit drbdadm status all | tee -a ${DRBD_LOGFILE}
    ;;
  84)
    logit cat /proc/drbd | tee -a ${DRBD_LOGFILE}
    ;;
  *)
    echo "Error! Wrong DRBD version."
esac
