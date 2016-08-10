#!/bin/bash

f_usage()
{
    echo "scpFils2Guest.sh <CLUSTER_CONF> <CTS_DIR>"
    echo "	<CLUSTER_CONF> - Basic configuration about cluster"
    echo "	<CTS_CONF> - Configuration to control ocfs2 test"
    echo "	<CTS_DIR> - Where ocfs2 CTS will be running"
    exit 1
}

if [ $# -ne 3 ]
then
    f_usage
    exit 1
fi

CLUSTER_CONF=$1
CTS_CONF=$2
CTS_DIR=$3

# Copy scripts to guest
for ip in `cat $CLUSTER_CONF |grep IP_NODE |cut -d "=" -f 2`
do
{
    echo "ssh root@${ip} mkdir -p ${CTS_DIR}"
    ssh root@${ip} "mkdir -p ${CTS_DIR}"

    echo "scp ${CTS_CONF} root@${ip}:${CTS_DIR}"
    scp ${CTS_CONF} root@${ip}:${CTS_DIR}


    echo "scp guest/* root@${ip}:${CTS_DIR}"
    scp guest/* root@${ip}:${CTS_DIR}

    echo  "ssh root@${ip} chmod 0600 /root/.ssh/id_rsa"
    ssh root@${ip} "chmod 0600 /root/.ssh/id_rsa"
} &
done
wait

# Pull test results into host after test done

#source $CLUSTER_CONF
#ip=`cat $CLUSTER_CONF | grep -A 1 ${master_node} | grep IP_NODE | cut -d "=" -f 2`
#echo scp -r root@${ip}:/usr/local/ocfs2-test/log ${BUILD_LOG_DIR_IN_HOST}
#scp -r root@${ip}:/usr/local/ocfs2-test/log ${BUILD_LOG_DIR_IN_HOST}

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
