#!/bin/bash

f_usage()
{
    echo "downloadTestLogs.sh <MASTER_NODE_IP> <BUILD_LOG_DIR_IN_HOST>"
    echo "	<MASTER_NODE_IP>: IP of the node where ocfs2 test starts"
    echo "	<BUILD_LOG_DIR_IN_HOST>: where the test logs go to"
}

if [ $# -ne 2 ]
then
    f_usage
    exit 1
fi

MASTER_NODE_IP=$1
BUILD_LOG_DIR_IN_HOST=$2

# Pull test results into host server after testing done

echo scp -r root@${MASTER_NODE_IP}:/usr/local/ocfs2-test/log ${BUILD_LOG_DIR_IN_HOST}
scp -r root@${MASTER_NODE_IP}:/usr/local/ocfs2-test/log ${BUILD_LOG_DIR_IN_HOST}

echo scp -r root@${MASTER_NODE_IP}:/var/lib/ocfs2test/test_o2lock.log ${BUILD_LOG_DIR_IN_HOST}
scp -r root@${MASTER_NODE_IP}:/var/lib/ocfs2test/test_o2lock.log ${BUILD_LOG_DIR_IN_HOST}

# remove all for the next run
echo ssh root@${MASTER_NODE_IP} rm -rf /usr/local/ocfs2-test/log/*
ssh root@${MASTER_NODE_IP} rm -rf /usr/local/ocfs2-test/log/*

echo ssh root@${MASTER_NODE_IP} rm -f /var/lib/ocfs2test/test_o2lock.log
ssh root@${MASTER_NODE_IP} rm -f /var/lib/ocfs2test/test_o2lock.log
