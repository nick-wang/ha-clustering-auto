#!/bin/bash
function usage()
{
  echo "cpCtsFilesToGuest.sh <CTS_CONF> <CLUSTER_CONF> <WORKING_DIR_IN_GUEST> <BUILD_LOG_DIR_IN_HOST>"
  exit
}

if [ $# -ne 4 ]
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

source $CLUSTER_CONF
scp root@${IP_NODE1}:/tmp/cts-configuration/my.log $4
echo "scp root@${IP_NODE1}:/tmp/cts-configuration/my.log $4"

for ip in `cat $CLUSTER_CONF |grep IP_NODE |cut -d "=" -f 2`
do
{
	date_str=`date +%s`
	hb_report="hb_report_${ip}_${date_str}"
	ssh root@${ip} "systemctl start pacemaker; sleep 3; hb_report -f 0:00 $hb_report"
        echo "ssh root@${ip}" "systemctl start pacemaker; sleep 3; hb_report -f 0:00 $hb_report"
	scp ${ip}:/root/$hb_report* $4
}
done
