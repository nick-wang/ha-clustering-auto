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
  ssh root@${ip} "rpm -qa|grep drbd>${TEMP_DIR}/drbd-rpm"
  ssh root@${ip} "rpm -qa>${TEMP_DIR}/all-rpms"
  sle_ver=($(ssh root@${ip} ". /var/lib/cluster-configuration/scripts/functions; getSLEVersion"))
  case ${sle_ver[0]} in
    12)
      ssh root@${ip} "cat /proc/drbd>${TEMP_DIR}/drbd-proc; drbd-overview>${TEMP_DIR}/drbd-overview; drbdadm dump >${TEMP_DIR}/drbdadm-dump"
      ;;
    *)
      ssh root@${ip} "cat /proc/drbd>${TEMP_DIR}/drbd-proc; drbdsetup status -vs >${TEMP_DIR}/drbdsetup-status; drbdadm dump >${TEMP_DIR}/drbdadm-dump"
      ;;
  esac
  ssh root@${ip} "crm configure show>${TEMP_DIR}/crm-ra; crm_mon -1>${TEMP_DIR}/crm_mon"
  ssh root@${ip} "drbdadm status all>${TEMP_DIR}/drbd9-status 2>&1"
  ssh root@${ip} "journalctl >/var/log/messages-journalctl 2>/dev/null"

  scp root@${ip}:/etc/drbd.conf ${LOG_DIR}/${ip}_drbd
  scp root@${ip}:/etc/drbd.d/* ${LOG_DIR}/${ip}_drbd
  scp root@${ip}:/var/log/messages* ${LOG_DIR}/${ip}_drbd 2>/dev/null
  scp root@${ip}:${TEMP_DIR}/* ${LOG_DIR}/${ip}_drbd
  scp root@${ip}:/var/log/drbd-log-* ${LOG_DIR}/${ip}_drbd
  scp root@${ip}:/var/log/rpm-* ${LOG_DIR}/${ip}_drbd 2>/dev/null
  scp -r root@${ip}:/var/log/pacemaker ${LOG_DIR}/${ip}_drbd 2>/dev/null

} &
done

wait
