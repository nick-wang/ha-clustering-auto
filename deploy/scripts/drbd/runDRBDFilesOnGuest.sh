#!/bin/bash
function usage()
{
  echo "runDRBDFilesOnGuest.sh <CLUSTER_CONF_IN_HOST> <WORKING_DIR_IN_GUEST> <HOW_MANY_DISKS_TO_PATITION>"
  echo "<HOW_MANY_DISKS_TO_PARTITION> should equal <HOW_MANY_DISKS_TO_ADD> of addVirioDisk.sh"
}

if [ $# -ne 3 ]
then
  usage
  exit -1
fi

#Import ENV conf
. functions

CLUSTER_CONF=$1
CLUSTER_DIR=$2
DISK_NUM=$3

for ip in `cat $CLUSTER_CONF |grep IP_NODE |cut -d "=" -f 2`
do
{
  ssh root@${ip} "mkdir -p ${CLUSTER_DIR}/template/drbd; mkdir -p ${CLUSTER_DIR}/scripts/drbd"
  
  # Copy the necessary drbd template from host to nodes
  scp drbd/crmDRBD.sh drbd/firstInitDRBD.sh drbd/make_part_drbd.sh \
      drbd/configDRBD.sh drbd/drbd_functions root@${ip}:${CLUSTER_DIR}/scripts/drbd/
  scp ../template/drbd/drbd_*_template root@${ip}:${CLUSTER_DIR}/template/drbd/
  
  # Partitioning all the disks
  nextPhase "Run 'drbd/make_part_drbd.sh' on each nodes:"
  ssh root@${ip} "cd ${CLUSTER_DIR}; ${CLUSTER_DIR}/scripts/drbd/make_part_drbd.sh ${DISK_NUM}"

  # Configure drbd resources configure and create meta-disk
  i=1
  while [ $i -le ${DISK_NUM} ]
  do
    temp=$(nconvert ${i})
    disk=/dev/vd${temp}
    nextPhase "Run 'drbd/configDRBD.sh' on each nodes:"
    if [ ${DISK_NUM} -ne 1 ]
    then
      ssh root@${ip} "cd ${CLUSTER_DIR}; ${CLUSTER_DIR}/scripts/drbd/configDRBD.sh ${disk} ${DISK_NUM}-"
    else
      ssh root@${ip} "cd ${CLUSTER_DIR}; ${CLUSTER_DIR}/scripts/drbd/configDRBD.sh ${disk}"
    fi
    i=$((i+1))
  done

  # Start the first sync to mark the sync source/target
  nextPhase "Run 'drbd/firstInitDRBD.sh' on each nodes:"
  ssh root@${ip} "cd ${CLUSTER_DIR}; ${CLUSTER_DIR}/scripts/drbd/firstInitDRBD.sh"

  # Add crm resources
  nextPhase "Run 'drbd/crmDRBD.sh' on each nodes:"
  ssh root@${ip} "cd ${CLUSTER_DIR}; ${CLUSTER_DIR}/scripts/drbd/crmDRBD.sh"
} &
done

wait
