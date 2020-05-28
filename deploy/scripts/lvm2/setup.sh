#!/bin/bash

#Import ENV conf
. functions

CLUSTER_CONF=$1
LOG_DIR=$2
run_script=$3

TEST_DIR="/root/lvm2-tst"

nextPhase "copy test script to target nodes"
cpToNodes ${CLUSTER_CONF} lvm2/${run_script} ${TEST_DIR}

nextPhase "install rpm packages for testing"
runOnAllNodes ${CLUSTER_CONF} "zypper install -y lvm2-testsuite mdadm"

sleep 3

node1_ip=`cat ${CLUSTER_CONF} |grep IP_NODE1 |cut -d "=" -f 2`
node2_ip=`cat ${CLUSTER_CONF} |grep IP_NODE2 |cut -d "=" -f 2`
MASTER_NODE="`cat ${CLUSTER_CONF} | grep HOSTNAME_NODE1 | cut -d"=" -f2`"

# $4 use to control testsuite running on 1 or 2 nodes
# if $4 non-exist, only run lvm2 on single node.
# please note, this is not cluster/local option.
if [ ! -n "$4" ]; then
	# only running on one node
	SINGLE_NODE=1
	IP[0]=${node1_ip}
else
	# hard code to 2, may set $4 in the future
	SINGLE_NODE=2
	IP[0]=${node1_ip}
	IP[1]=${node2_ip}
fi

for i in ${IP[*]}; do
{
	nextPhase "running test suite on ${i}"
	ssh root@${i} "cd ${TEST_DIR}; ./${run_script} ${MASTER_NODE}"

	nextPhase "collection test suites log"
	scp -r root@${i}:${TEST_DIR} ${LOG_DIR}/${i}
} &
done

wait

nextPhase "create node1 & node2 differ result on host"
cd ${LOG_DIR}/ 
if [ ${SINGLE_NODE} -ne 1 ];then
	diff -Nupr ${node1_ip}/list ${node2_ip}/list > list.diff
else
	mkdir ${node2_ip}
	cp ${node1_ip}/list ${node2_ip}/
	echo "using node1 result as node2 result"  > list.diff
fi

exit 0
