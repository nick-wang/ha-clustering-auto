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
sleep 10

#Reboot when all resources finished sync
if [ x"$(isDRBD9)" == x"true" ]
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
    sleep 90
  
    cat /proc/drbd |grep "sync'ed:" >/dev/null 2>&1
  done
  
  logit cat /proc/drbd
fi
echo "Finished first sync."

# Downgrade to secondary and stop drbd
isMaster "$HOSTNAME_NODE1"
if [ $? -eq 0 ]
then
  logit drbdadm secondary all
fi
sleep 5
