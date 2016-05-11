#!/bin/bash
function usage()
{
  echo "collectLogs.sh <CLUSTER_CONF_IN_HOST> <LOG_DIR_IN_HOST>"
}

if [ $# -ne 2 ]
then
  usage
  exit -1
fi

TEMP_DIR="/root/drbdlog/"

#Import ENV conf
. functions

CLUSTER_CONF=$1
LOG_DIR=$2


for ip in `cat $CLUSTER_CONF |grep IP_NODE |cut -d "=" -f 2`
do
{
  mkdir -p ${LOG_DIR}/${ip}_drbd
  ssh root@${ip} "mkdir -p ${TEMP_DIR}"
  ssh root@${ip} "rpm -qa|grep drbd >${TEMP_DIR}/rpm"
  ssh root@${ip} "cat /proc/drbd >${TEMP_DIR}/proc; drbd-overview>${TEMP_DIR}/overview"
  ssh root@${ip} "crm configure show >${TEMP_DIR}/ra; crm_mon -1 >${TEMP_DIR}/crm_mon"

  scp root@${ip}:/etc/drbd* ${LOG_DIR}/${ip}_drbd
  scp root@${ip}:/var/log/message ${LOG_DIR}/${ip}_drbd
  scp root@${ip}:~/drbdlog/* ${LOG_DIR}/${ip}_drbd
  
} &
done

wait
