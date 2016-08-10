#!/bin/bash
#
# runCts.sh   <CTS_CONF>
# 
# Run ocfs2 CTS	

source ~/.bash_profile

f_usage()
{ 
	echo "Usage: `basename ${0}` <CTS_CONF>" 
	exit 1
}

f_info()
{
	echo [INFO]@{`hostname`} $*
}

f_log()
{
	echo [LOG]@{`hostname`} $*
}

f_umount()
{
	dev=`mount -t ocfs2`

	if [ -n "$dev" ];then
		f_log "sudo umount /mnt/ocfs2"
		sudo umount /mnt/ocfs2
	fi
}

if [ $# -ne "1" ];then
	f_usage
	exit 1
fi

CTS_CONF="$1"

f_info "Dump configuration file for ocfs2 test:"
cat ${CTS_CONF}	

BLOCKSIZE="`cat ${CTS_CONF} | grep BLOCK_SIZE | cut -d "=" -f 2`"
CLUSTERSIZE="`cat ${CTS_CONF} | grep CLUSTER_SIZE | cut -d "=" -f 2`"
TESTMODE="`cat ${CTS_CONF} | grep TESTMODE | cut -d "=" -f 2`"
TESTMODE="`cat ${CTS_CONF} | grep TESTMODE | cut -d "=" -f 2`"
SINGLE_CASES="`cat ${CTS_CONF} | grep SINGLE_CASES | cut -d "=" -f 2`"
MULTIPLE_CASES="`cat ${CTS_CONF} | grep MULTIPLE_CASES | cut -d "=" -f 2`"
CLUSTER_STACK="`cat ${CTS_CONF} | grep CLUSTER_STACK | cut -d "=" -f 2`"
CLUSTER_NAME="`cat ${CTS_CONF} | grep CLUSTER_NAME | cut -d "=" -f 2`"

# __MAIN__

# Problematic cases

# 1. single node test
#
# mmaptruncate: patch v3
# reflink: upstream
#
# reserve_space: device

# 2. multiple node test
#
# cross_delete: unknown
#
# lvb_torture: unknown

if [ X"$TESTMODE" == X"single" -o X"$TESTMODE" == X"all" ];then
	echo -e "\n\n\n"
	f_info "Start single node testing..."

	f_log "single_run-WIP.sh -k /usr/local/ocfs2-test/tmp/linux-2.6.39.tar.gz -l /usr/local/ocfs2-test/log -m /mnt/ocfs2/ -d /dev/disk/by-path/ip-147.2.207.237:3260-iscsi-eric.2015-12.suse.bej:ocfs2-san2-lun-0 -b ${BLOCKSIZE} -c ${CLUSTERSIZE} -s ${CLUSTER_STACK} -n ${CLUSTER_NAME} -t ${SINGLE_CASES}"

	single_run-WIP.sh -k  /usr/local/ocfs2-test/tmp/linux-2.6.39.tar.gz -l /usr/local/ocfs2-test/log -m /mnt/ocfs2/ -d /dev/disk/by-path/ip-147.2.207.237:3260-iscsi-eric.2015-12.suse.bej:ocfs2-san2-lun-0 -b ${BLOCKSIZE} -c ${CLUSTERSIZE}  -s ${CLUSTER_STACK} -n ${CLUSTER_NAME} -t ${SINGLE_CASES} &	

	wait
	f_info "DONE: single node testing"
fi

f_umount

sleep 5


if [ X"$TESTMODE" == X"multiple" -o X"$TESTMODE" == X"all" ];then
	echo -e "\n\n\n"
	f_info "Start multiple nodes testing..."

	f_log "multiple_run.sh -k /usr/local/ocfs2-test/tmp/linux-2.6.39.tar.gz -n ocfs2cts1,ocfs2cts2 -d /dev/disk/by-path/ip-147.2.207.237:3260-iscsi-eric.2015-12.suse.bej:ocfs2-san2-lun-0 -b ${BLOCKSIZE} -c ${CLUSTERSIZE}  -s ${CLUSTER_STACK} -C ${CLUSTER_NAME} -t ${MULTIPLE_CASES}  /mnt/ocfs2"

	multiple_run.sh -k /usr/local/ocfs2-test/tmp/linux-2.6.39.tar.gz -n ocfs2cts1,ocfs2cts2 -d /dev/disk/by-path/ip-147.2.207.237:3260-iscsi-eric.2015-12.suse.bej:ocfs2-san2-lun-0 -b ${BLOCKSIZE} -c ${CLUSTERSIZE} -t ${MULTIPLE_CASES}  -s ${CLUSTER_STACK} -C ${CLUSTER_NAME}  /mnt/ocfs2 &

	wait
	f_info "DONE: multiple nodes testing"
fi
