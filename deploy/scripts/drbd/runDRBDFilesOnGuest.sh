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

for ip in `cat $CLUSTER_CONF |grep IP_NODE |cut -d "=" -f 2`
do
{
  ssh root@${ip} "mkdir -p ${CLUSTER_DIR}/template/drbd; mkdir -p ${CLUSTER_DIR}/scripts/drbd"

  # Copy the necessary drbd template from host to nodes
  scp drbd/crmDRBD.sh drbd/firstInitDRBD.sh drbd/make_part_drbd.sh \
      drbd/configDRBD.sh drbd/drbd_functions root@${ip}:${CLUSTER_DIR}/scripts/drbd/
  scp ../template/drbd/drbd_*_template root@${ip}:${CLUSTER_DIR}/template/drbd/

  # Partitioning all the disks
  ssh root@${ip} "cd ${CLUSTER_DIR}; ${CLUSTER_DIR}/scripts/drbd/make_part_drbd.sh ${DISK_NUM}"

  # Configure drbd resources configure and create meta-disk
  temp=$(nconvert ${DISK_NUM})
  disk=/dev/vd${temp}
  ssh root@${ip} "cd ${CLUSTER_DIR}; ${CLUSTER_DIR}/scripts/drbd/configDRBD.sh ${disk} ${DISK_NUM}"

  # Start the first sync to mark the sync source/target
  # TODO: Testing call this script multiple times.
  if [ $SKIP_SYNC -ne 1 ]
  then
    ssh root@${ip} "cd ${CLUSTER_DIR}; ${CLUSTER_DIR}/scripts/drbd/firstInitDRBD.sh"
  fi
} &
done
wait

# Waiting for all nodes finished first init
for ip in `cat $CLUSTER_CONF |grep IP_NODE |cut -d "=" -f 2`
do
{
  # Add crm resources
  ssh root@${ip} "cd ${CLUSTER_DIR}; ${CLUSTER_DIR}/scripts/drbd/crmDRBD.sh"
} &
done
wait
