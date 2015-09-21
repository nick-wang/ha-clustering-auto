#!/bin/bash
function usage()
{
  echo "cpFilesToGuest.sh <CLUSTER_CONF_IN_HOST> <WORKING_DIR_IN_GUEST>"
  exit
}

CLUSTER_CONF=$1
CLUSTER_DIR=$2

for ip in `cat ../cluster_conf |grep IP_NODE |cut -d "=" -f 2`
do
{
ssh root@${ip} "mkdir -p ${CLUSTER_DIR}/templete; mkdir -p ${CLUSTER_DIR}/scripts"

scp ./configCluster.sh ./functions root@${ip}:${CLUSTER_DIR}/scripts/
scp ${CLUSTER_CONF} root@${ip}:${CLUSTER_DIR}
scp ../templete/*_templete root@${ip}:${CLUSTER_DIR}/templete/

ssh root@${ip} "cd ${CLUSTER_DIR}; ${CLUSTER_DIR}/scripts/configCluster.sh "
} &
done

# Wait all sub process to finish
wait
