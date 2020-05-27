#!/bin/bash

#Import ENV conf
. functions

CLUSTER_CONF=$1
LOG_DIR=$2
run_script=$3

# $4 use to control testsuite running on 1 or 2 nodes
# if $4 non-exist, only run lvm2 on single node.
# please note, this is not cluster/local option.
if [ ! -n "$4" ]; then
	# only running on one node
	SINGLE_NODE=1
else
	# hard code to 2
	SINGLE_NODE=2
fi

TEST_DIR="/root/lvm2-tst"

nextPhase "copy test script to target nodes"
cpToNodes ${CLUSTER_CONF} lvm2/${run_script} ${TEST_DIR}

nextPhase "install rpm packages for testing"
runOnAllNodes ${CLUSTER_CONF} "zypper install -y lvm2-testsuite mdadm"

sleep 3

node1_ip=`cat ${CLUSTER_CONF} |grep IP_NODE1 |cut -d "=" -f 2`
node2_ip=`cat ${CLUSTER_CONF} |grep IP_NODE2 |cut -d "=" -f 2`
MASTER_NODE="`cat ${CLUSTER_CONF} | grep HOSTNAME_NODE1 | cut -d"=" -f2`"

if [ ${SINGLE_NODE} -ne 1 ];then
	nextPhase "running test suite on both nodes"
	runOnAllNodes ${CLUSTER_CONF} "cd ${TEST_DIR}; ./${run_script} ${MASTER_NODE}"

	nextPhase "collection test suites log"
	for ip in `cat $CLUSTER_CONF |grep IP_NODE |cut -d "=" -f 2`; do
	{
		scp -r root@${ip}:${TEST_DIR} ${LOG_DIR}/${ip}
	} &
	done

	wait

	nextPhase "create node1 & node2 differ result on host"
	cd ${LOG_DIR}/ 
	diff -Nupr ${node1_ip}/list ${node2_ip}/list > ${LOG_DIR}/list.diff
else
	nextPhase "running test suite on ${HOSTNAME_NODE1}"
	ssh root@${node1_ip} "cd ${TEST_DIR}; ./${run_script} ${MASTER_NODE}"

	
	nextPhase "collection test suites log"
	scp -r root@${node1_ip}:${TEST_DIR} ${LOG_DIR}/${node1_ip}
	# use node1 result to create node2 folder. This makes testcases/parseLVM2Report.py happy.
	mkdir ${LOG_DIR}/${node2_ip}
	cp ${LOG_DIR}/${node1_ip}/list ${LOG_DIR}/${node2_ip}/
fi

exit 0
