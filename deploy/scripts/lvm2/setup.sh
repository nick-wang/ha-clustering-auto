#!/bin/bash

#Import ENV conf
. functions

CLUSTER_CONF=$1
LOG_DIR=$2
run_script=$3
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

	nextPhase "wait for completion"
	checkAllFinish ${CLUSTER_CONF} ${TEST_DIR}/complete.txt
	
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

	nextPhase "wait for completion"
	while :
	do
		ssh root@${node1_ip} "ls ${TEST_DIR}/complete.txt >/dev/null 2>&1"
		if [ $? -eq 0 ]; then
			break
		fi
		sleep 10
	done
	
	nextPhase "collection test suites log"
	scp -r root@${node1_ip}:${TEST_DIR} ${LOG_DIR}/${node1_ip}
	# use node1 result to create node2 folder. This makes testcases/parseLVM2Report.py happy.
	mkdir ${LOG_DIR}/${node2_ip}
	cp ${LOG_DIR}/${node1_ip}/list ${LOG_DIR}/${node2_ip}/
fi

exit 0
