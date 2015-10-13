#!/bin/bash
function usage()
{
  echo "cpCtsFilesToGuest.sh <CTS_CONF> <CLUSTER_CONF> <WORKING_DIR_IN_GUEST>"
  exit
}

function isMaster()
{
    # Usage:
    #     isMaster <nodename>
    if [ $# -ne 1 ]
    then 
        return 1
    fi

    LOCALHOST=$(uname -n|cut -d "." -f 1)

    if [ "$1" == "$LOCALHOST" ]
    then
        #Master node
        return 0
    else
        return 1
    fi
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

for hostname in `cat $CLUSTER_CONF | grep HOSTNAME_NODE | cut -d "=" -f 2`
do
    isMaster $hostname
	if [ $? -eq 0 ]; then
		scp $hostname:/tmp/cts-confihuration/my.log $4
	fi
done
wait
