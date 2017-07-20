#!/bin/bash

f_usage()
{
	echo "downloadTestLogs.sh <MASTER_NODE_IP> <BUILD_LOG_DIR_IN_HOST>"
	echo "	<MASTER_NODE_IP>: IP of the node where lvm2 test starts"
	echo "	<BUILD_LOG_DIR_IN_HOST>: where the test logs go to"
}

if [ $# -ne 2 ]
then
	f_usage
	exit 1
fi

MASTER_NODE_IP=$1
BUILD_LOG_DIR_IN_HOST=$2

LOG_DIR=/var/log/qa/ctcs2/
runner_log=/tmp/test_lvm2_2_02_120-run.log

# Pull test results into host server after testing done

echo scp -r root@${MASTER_NODE_IP}:${LOG_DIR} ${BUILD_LOG_DIR_IN_HOST}
scp -r root@${MASTER_NODE_IP}:${LOG_DIR} ${BUILD_LOG_DIR_IN_HOST}

echo scp root@${MASTER_NODE_IP}:"$runner_log" ${BUILD_LOG_DIR_IN_HOST}
scp root@${MASTER_NODE_IP}:"$runner_log" ${BUILD_LOG_DIR_IN_HOST}

# cleanup the logs in guest
echo ssh root@${MASTER_NODE_IP} rm -rf ${LOG_DIR}/*
ssh root@${MASTER_NODE_IP} rm -rf ${LOG_DIR}/*

echo  ssh root@${MASTER_NODE_IP} rm -rf "$runner_log"
ssh root@${MASTER_NODE_IP} rm -rf "$runner_log"

TEST_REPORTS_DIR=${BUILD_LOG_DIR_IN_HOST}/test_reports
echo mkdir ${TEST_REPORTS_DIR}
mkdir ${TEST_REPORTS_DIR}
echo find ${BUILD_LOG_DIR_IN_HOST} -name test_results -exec cp '{}' ${TEST_REPORTS_DIR} \;
find ${BUILD_LOG_DIR_IN_HOST} -name test_results -exec cp '{}' ${TEST_REPORTS_DIR} \;
