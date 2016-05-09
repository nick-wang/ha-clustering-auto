#!/bin/bash

#Import ENV conf
. cluster_conf
. scripts/functions
. scripts/drbd/drbd_functions

#Go primary for the initial sync
isMaster "$HOSTNAME_NODE1"
if [ $? -eq 0 ]
then
  drbdadm primary --force all
fi
sleep 5

#Reboot when all resources finished sync
if [ $(isDRBD9)=="true" ]
then
  #TBD:
  # Check sync progress in drbd9
  drbdadm status all
else
  # Check sync progress in drbd8
  cat /proc/drbd |grep "sync'ed:" >/dev/null 2>&1
  while [ $? -eq 0 ]
  do
    logit cat /proc/drbd
    sleep 60
  
    cat /proc/drbd |grep "sync'ed:" >/dev/null 2>&1
  done
  
  logit cat /proc/drbd
fi
echo "Finished first sync."