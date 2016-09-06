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
  infoLog "Make Primary on $HOSTNAME_NODE1"
  drbdadm primary --force all
fi
sleep 3

#Reboot when all resources finished sync
case $(getDRBDVer) in
  9)
    # Log the drbd9 version
    infoRun cat /proc/drbd | tee -a ${DRBD_LOGFILE}

    drbdadm status all |grep "done:" >/dev/null 2>&1
    while [ $? -eq 0 ]
    do
      debugRun drbdadm status all
      sleep 90

      drbdadm status all |grep "done:" >/dev/null 2>&1
    done

    nextPhase "Finished the first sync." | tee -a ${DRBD_LOGFILE}
    infoRun drbdadm status all | tee -a ${DRBD_LOGFILE}
    ;;
  84)
    # Check sync progress in drbd8
    cat /proc/drbd |grep "sync'ed:" >/dev/null 2>&1
    while [ $? -eq 0 ]
    do
      debugRun cat /proc/drbd
      sleep 90

      cat /proc/drbd |grep "sync'ed:" >/dev/null 2>&1
    done

    nextPhase "Finished the first sync." | tee -a ${DRBD_LOGFILE}
    infoRun cat /proc/drbd | tee -a ${DRBD_LOGFILE}
    ;;
  *)
    echo "Error! Wrong DRBD version."
esac

# Downgrade to secondary
isMaster "$HOSTNAME_NODE1"
if [ $? -eq 0 ]
then
  drbdadm secondary all
fi
sleep 3
