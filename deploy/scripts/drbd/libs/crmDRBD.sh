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
  infoRun crm configure show | tee -a ${DRBD_LOGFILE}

  #Disable stonith, in case error happened, one always fence the other
  crm configure property stonith-enabled="true"

  tempfile=drbd-tempfile
  for resname in `drbdadm dump all |grep -P "^resource .+ {" | cut -d " " -f 2`
  do
    echo "configure
          primitive res-${resname} ocf:linbit:drbd \
                    params drbd_resource=${resname} \
                    op monitor interval=10s timeout=20s\
                    op notify timeout=120 \
                    op start timeout=240 \
                    op stop timeout=100" > $tempfile

    case $(getDRBDVer) in
      9)
        echo "
        ms ms_${resname} res-${resname} \
           meta master-max=1 master-node-max=1 \
           meta clone-max=${NODES} clone-node-max=1 \
           meta notify=true target-role=Started" >> $tempfile
        ;;
      84)
        echo "
        ms ms_${resname} res-${resname} \
           meta master-max=1 master-node-max=1 \
           meta clone-max=2 clone-node-max=1 \
           meta notify=true target-role=Started" >> $tempfile

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
        ;;

      *)
        echo "Error! Wrong DRBD version."
    esac

    crm -f ${tempfile}
  done

  nextPhase "After configuring DRBD" | tee -a ${DRBD_LOGFILE}
  infoRun crm configure show | tee -a ${DRBD_LOGFILE}
  sleep 3
else
  #Waiting Node1 to configure resources
  sleep 8
fi

# Run on each node for each resource
# Make sure all connection up before testing
#
# Sometimes may failed by connection shutdown
# One node:
#   drbd_send_ping has failed (Connection reset by peer)
#   ...
#   Failed to create workqueue ack_sender
# The other node:
#   sock was shut down by peer
#
sleep 20  # waiting to drbd start
for res in `drbdadm sh-resources`
do
  reconnectStandAloneRes $res
done

infoRun crm_mon -1 | tee -a ${DRBD_LOGFILE}
case $(getDRBDVer) in
  9)
    infoRun drbdadm status all | tee -a ${DRBD_LOGFILE}
    ;;
  84)
    infoRun cat /proc/drbd | tee -a ${DRBD_LOGFILE}
    ;;
  *)
    echo "Error! Wrong DRBD version."
esac
