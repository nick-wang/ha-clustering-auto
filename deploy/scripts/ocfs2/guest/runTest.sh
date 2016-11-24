#!/bin/bash
#
# runCts.sh   <CTS_CONF> <NODE_LIST>
#
# Run ocfs2 CTS

source ~/.bash_profile

f_usage()
{
	echo "Usage: `basename ${0}` <CTS_CONF> <NODE_LIST>"
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
	for node in `echo ${NODE_LIST} | sed "s:,: :g"`
	do
		echo "ssh ${node} sudo umount /mnt/ocfs2 > /dev/null 2>&1"
		ssh ${node} "sudo umount /mnt/ocfs2 > /dev/null 2>&1"
	done
}

if [ $# -lt "2" ];then
	f_usage
	exit 1
fi

CTS_CONF="$1"
NODE_LIST="$2"

f_info "Dump configuration file for ocfs2 test:"
cat ${CTS_CONF}

BLOCKSIZE="`cat ${CTS_CONF} | grep BLOCK_SIZE | cut -d "=" -f 2`"
CLUSTERSIZE="`cat ${CTS_CONF} | grep CLUSTER_SIZE | cut -d "=" -f 2`"
TESTMODE="`cat ${CTS_CONF} | grep TESTMODE | cut -d "=" -f 2`"
SINGLE_CASES="`cat ${CTS_CONF} | grep SINGLE_CASES | cut -d "=" -f 2`"
MULTIPLE_CASES="`cat ${CTS_CONF} | grep MULTIPLE_CASES | cut -d "=" -f 2`"
CLUSTER_STACK="`cat ${CTS_CONF} | grep CLUSTER_STACK | cut -d "=" -f 2`"
CLUSTER_NAME="`cat ${CTS_CONF} | grep CLUSTER_NAME | cut -d "=" -f 2`"
SHARED_DISK="`cat ${CTS_CONF} | grep SHARED_DISK | cut -d "=" -f 2`"
KERNEL_SOURCE="`cat ${CTS_CONF} | grep KERNEL_SOURCE | cut -d "=" -f 2`"

# exit if TESTMODE == none
if [ ${TESTMODE} == "none" ];then
	f_info "testmode is none, so exit!"
	exit 0
fi

# Prepare kernel-source used by ocfs2 CTS
if [ ! -f ${KERNEL_SOURCE} ];then
	f_info "ERR: source kernel not found"
	exit 1
fi

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

	f_log "single_run-WIP.sh -k /usr/local/ocfs2-test/tmp/linux-2.6.39.tar.gz -l /usr/local/ocfs2-test/log -m /mnt/ocfs2/ -d ${SHARED_DISK} -b ${BLOCKSIZE} -c ${CLUSTERSIZE} -s ${CLUSTER_STACK} -n ${CLUSTER_NAME} -t ${SINGLE_CASES}"

	single_run-WIP.sh -k  /usr/local/ocfs2-test/tmp/linux-2.6.39.tar.gz -l /usr/local/ocfs2-test/log -m /mnt/ocfs2/ -d ${SHARED_DISK} -b ${BLOCKSIZE} -c ${CLUSTERSIZE}  -s ${CLUSTER_STACK} -n ${CLUSTER_NAME} -t ${SINGLE_CASES}

	f_info "DONE: single node testing"
fi

sleep 3
f_umount
sleep 3


if [ X"$TESTMODE" == X"multiple" -o X"$TESTMODE" == X"all" ];then
	echo -e "\n\n\n"
	f_info "Start multiple nodes testing..."

	f_log "multiple_run.sh -k /usr/local/ocfs2-test/tmp/linux-2.6.39.tar.gz -n ${NODE_LIST} -d ${SHARED_DISK} -b ${BLOCKSIZE} -c ${CLUSTERSIZE}  -s ${CLUSTER_STACK} -C ${CLUSTER_NAME} -t ${MULTIPLE_CASES}  /mnt/ocfs2"

	multiple_run.sh -k /usr/local/ocfs2-test/tmp/linux-2.6.39.tar.gz -n ${NODE_LIST} -d ${SHARED_DISK} -b ${BLOCKSIZE} -c ${CLUSTERSIZE} -t ${MULTIPLE_CASES}  -s ${CLUSTER_STACK} -C ${CLUSTER_NAME}  /mnt/ocfs2

	f_info "DONE: multiple nodes testing"
fi

if [ X"$TESTMODE" == X"single_discontig_bg" -o X"$TESTMODE" == X"all" ];then
	echo -e "\n\n\n"
	f_info "Start single-node discontig block group testing..."

	f_log "discontig_runner.sh -m ${NODE_LIST} -d ${SHARED_DISK} -b ${BLOCKSIZE} -c ${CLUSTERSIZE}  -s ${CLUSTER_STACK} -n ${CLUSTER_NAME} /mnt/ocfs2"

	discontig_runner.sh -d ${SHARED_DISK} -b ${BLOCKSIZE} -c ${CLUSTERSIZE}  -s ${CLUSTER_STACK} -n ${CLUSTER_NAME} /mnt/ocfs2

	f_info "DONE: single-node discontig block group testing"
fi

#if [ X"$TESTMODE" == X"multiple_discontig_bg" -o X"$TESTMODE" == X"all" ];then
if [ X"$TESTMODE" == X"multiple_discontig_bg" ];then
	echo -e "\n\n\n"
	f_info "Start multiple-node discontig block group testing..."

	f_log "discontig_runner.sh -m ${NODE_LIST} -d ${SHARED_DISK} -b ${BLOCKSIZE} -c ${CLUSTERSIZE}  -s ${CLUSTER_STACK} -n ${CLUSTER_NAME} /mnt/ocfs2"

	discontig_runner.sh -m ${NODE_LIST} -d ${SHARED_DISK} -b ${BLOCKSIZE} -c ${CLUSTERSIZE}  -s ${CLUSTER_STACK} -n ${CLUSTER_NAME} /mnt/ocfs2

	f_info "DONE: multiple-node discontig block group testing"
fi
