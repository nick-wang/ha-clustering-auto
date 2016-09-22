#!/bin/bash
function usage()
{
  echo "runDRBDFilesOnGuest.sh <CLUSTER_CONF_IN_HOST> <WORKING_DIR_IN_GUEST> <WHICH_DISK_TO_PARTITION> <SKIP_FIRST_SYNC>"
  echo "<WHICH_DISK_TO_PARTITION> should a number like 1, 2, 3, etc..."
  echo "SKIP FIRST SYNC when <SKIP_FIRST_SYNC> is 1, using when configuring multiple disks. eg. skip sync except the last config."
  echo "Should call this script multiple times for multiple disks."
}

if [ $# -lt 3 ] || [ $# -gt 4 ]
then
  usage
  exit -1
fi

#Import ENV conf
. functions

CLUSTER_CONF=$1
CLUSTER_DIR=$2
DISK_NUM=$3
SKIP_SYNC=${4:-0}

cpToNodes ${CLUSTER_CONF} "drbd/drbd_functions" "${CLUSTER_DIR}/scripts/drbd/"
cpToNodes ${CLUSTER_CONF} "drbd/libs/crmDRBD.sh drbd/libs/firstInitDRBD.sh drbd/libs/make_part_drbd.sh \
          drbd/libs/configDRBD.sh" "${CLUSTER_DIR}/scripts/drbd/libs"
cpToNodes ${CLUSTER_CONF} "../template/drbd/drbd_*_template" "${CLUSTER_DIR}/template/drbd/"

# Partitioning the disk
nextPhase "Launch make_part_drbd.sh (${CLUSTER_CONF})"
runOnAllNodes ${CLUSTER_CONF} "cd ${CLUSTER_DIR}; ${CLUSTER_DIR}/scripts/drbd/libs/make_part_drbd.sh ${DISK_NUM}"

# Configure drbd resources configure and create meta-disk
temp=$(nconvert ${DISK_NUM})
disk=/dev/vd${temp}
nextPhase "Launch configDRBD.sh (${CLUSTER_CONF})"
runOnAllNodes ${CLUSTER_CONF} "cd ${CLUSTER_DIR}; ${CLUSTER_DIR}/scripts/drbd/libs/configDRBD.sh ${disk} ${DISK_NUM}"

sleep 3

# Start the first sync to mark the sync source/target
if [ $SKIP_SYNC -ne 1 ]
then
nextPhase "Launch firstInitDRBD.sh (${CLUSTER_CONF})"
runOnAllNodes ${CLUSTER_CONF} "cd ${CLUSTER_DIR}; ${CLUSTER_DIR}/scripts/drbd/libs/firstInitDRBD.sh"
fi

nextPhase "Launch crmDRBD.sh (${CLUSTER_CONF})"
runOnAllNodes ${CLUSTER_CONF} "cd ${CLUSTER_DIR}; ${CLUSTER_DIR}/scripts/drbd/libs/crmDRBD.sh"
