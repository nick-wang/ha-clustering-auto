#!/bin/bash

#Import ENV conf
. cluster_conf
. scripts/functions
. scripts/drbd/drbd_functions

nextPhase "Launch $0"

#Go primary for the initial sync
isMaster "$HOSTNAME_NODE1"
if [ $? -eq 0 ]
then
  drbdadm primary --force all
fi
sleep 3

#Reboot when all resources finished sync
case $(getDRBDVer) in
  9)
    #TBD:
    # Check sync progress in drbd9
    drbdadm status all
    ;;
  84)
    # Check sync progress in drbd8
    cat /proc/drbd |grep "sync'ed:" >/dev/null 2>&1
    while [ $? -eq 0 ]
    do
      logit cat /proc/drbd
      sleep 90

      cat /proc/drbd |grep "sync'ed:" >/dev/null 2>&1
    done

    nextPhase "Finished the first sync." | tee -a ${DRBD_LOGFILE}
    logit cat /proc/drbd | tee -a ${DRBD_LOGFILE}
    ;;
  *)
    echo "Error! Wrong DRBD version."
esac

# Downgrade to secondary and stop drbd
isMaster "$HOSTNAME_NODE1"
if [ $? -eq 0 ]
then
  drbdadm secondary all
fi
sleep 3
