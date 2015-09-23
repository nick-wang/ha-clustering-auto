#!/bin/bash
function usage()
{
  echo "cpCtsFilesToGuest.sh <CTS_CONF> <CLUSTER_CONF> <WORKING_DIR_IN_GUEST>"
  exit
}

if [ $# -ne 3 ]
then
    usage
    exit -1
fi

CTS_CONF=$1
CLUSTER_CONF=$2
CTS_DIR=$3

for ip in `cat $CLUSTER_CONF |grep IP_NODE |cut -d "=" -f 2`
do
{
ssh root@${ip} "mkdir -p ${CTS_DIR}/; mkdir -p ${CTS_DIR}/scripts"

scp ../cts/configAndRunCts.sh ../scripts/functions root@${ip}:${CTS_DIR}/scripts/
scp ${CTS_CONF} ${CLUSTER_CONF} root@${ip}:${CTS_DIR}

ssh root@${ip} "chmod 0600 /root/.ssh/id_rsa;cd ${CTS_DIR}; ${CTS_DIR}/scripts/configAndRunCts.sh "
} &
done

wait