#!/bin/bash

f_usage()
{
    echo "cpCtsFilesToGuest.sh <CLUSTER_CONF> <WORKING_DIR_IN_GUEST> <BUILD_LOG_DIR_IN_HOST>"
    echo "	<CLUSTER_CONF> - Basic configuration about cluster"
    echo "	<WORKING_DIR_IN_GUEST> - Where ocfs2 CTS will be running"
    echo "	<BUILD_LOG_DIR_IN_HOST> - Where the test result will be stored"
    exit 1
}

if [ $# -ne 3 ]
then
    usage
    exit 1
fi

CLUSTER_CONF=$1
CTS_DIR=$2
BUILD_LOG_DIR_IN_HOST=$3

# Prepare test environment
trigger="runInGuest.sh"

# Invoke ocfs2 CTS
run_cts="runCts.sh"

# the node where we invoke test script
master_node="ocfs2cts1"

# Copy and run scripts in guest

for ip in `cat $CLUSTER_CONF |grep IP_NODE |cut -d "=" -f 2`
do
{
    echo "ssh root@${ip} mkdir -p ${CTS_DIR}"
    ssh root@${ip} "mkdir -p ${CTS_DIR}"

    echo "scp ${trigger} root@${ip}:${CTS_DIR}"
    scp ${trigger} root@${ip}:${CTS_DIR}

    echo "scp ${run_cts} root@${ip}:${CTS_DIR}"
    scp ${run_cts} root@${ip}:${CTS_DIR}

    echo  "ssh root@${ip} chmod 0600 /root/.ssh/id_rsa; cd ${CTS_DIR}; ${CTS_DIR}/${trigger}"
    ssh root@${ip} "chmod 0600 /root/.ssh/id_rsa; cd ${CTS_DIR}; ${CTS_DIR}/${trigger}"
} &
done
wait

# Pull test results into host after test done

source $CLUSTER_CONF
ip=`cat $CLUSTER_CONF | grep -A 1 ${master_node} | grep IP_NODE | cut -d "=" -f 2`
echo scp -r root@${ip}:/usr/local/ocfs2-test/log ${BUILD_LOG_DIR_IN_HOST}
scp -r root@${ip}:/usr/local/ocfs2-test/log ${BUILD_LOG_DIR_IN_HOST}

# TODO: decorate test result

#for ip in `cat $CLUSTER_CONF |grep IP_NODE |cut -d "=" -f 2`
#do
#{
#ip=`cat $CLUSTER_CONF | grep IP_NODE |cut -d "=" -f 2 | head -1`
#date_str=`date +%s`
#hb_report="hb_report_${ip}_${date_str}"
#ssh root@${ip} "systemctl restart pacemaker; sleep 3; hb_report -f 0:00 $hb_report"
#echo "ssh root@${ip}" "systemctl start pacemaker; sleep 3; hb_report -f 0:00 $hb_report"
#scp ${ip}:/root/$hb_report* $3
#}
#done
