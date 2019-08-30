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

f_do_on_each_node()
{
	CMD=$1

	for node in `echo ${NODE_LIST} | sed "s:,: :g"`
	do
		echo "ssh ${node} $CMD"
		ssh ${node} $CMD
	done
}

f_umount()
{
	f_do_on_each_node "sudo umount ${MOUNT_POINT} > /dev/null 2>&1"
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
MOUNT_POINT="`cat ${CTS_CONF} | grep MOUNT_POINT | cut -d "=" -f 2`"
HOST_IP="`cat ${CTS_CONF} | grep HOST_IP | cut -d "=" -f 2`"
KERNEL_SOURCE="`cat ${CTS_CONF} | grep KERNEL_SOURCE | cut -d "=" -f 2`"

# exit if TESTMODE == none
if [ ${TESTMODE} == "none" ];then
	f_info "testmode is none, don't run any testcase!"
	exit 0
fi

if [ -z ${SHARED_DISK} ]; then
	f_info "ERR: shared disk not specified"
	exit 1
fi

if [ -z ${MOUNT_POINT} ]; then
	f_info "ERR: mount point not specified"
	exit 1
fi

if [ -z ${KERNEL_SOURCE} ]; then
	f_info "ERR: source kernel not found"
	exit 1
fi

# Deal with blocksize and clustersize
if [ ! -z "$BLOCKSIZE" ]; then
	BLOCKSIZE="-b ${BLOCKSIZE}"
else
	BLOCKSIZE=
fi

if [ ! -z "$CLUSTERSIZE" ]; then
	CLUSTERSIZE="-c ${CLUSTERSIZE}"
else
	CLUSTERSIZE=
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

# Create mount point
f_info "Create mount point"
f_do_on_each_node "sudo mkdir -p ${MOUNT_POINT}"
f_do_on_each_node "sudo chmod 777 ${MOUNT_POINT}"

# Prepare kernel-source used by some test cases
#f_info "Prepare kernel-source used by some test cases"
#f_log "scp root@${HOST_IP}:${KERNEL_SOURCE} /usr/local/ocfs2-test/tmp"

# we cannot access to host passwordlessly, pity
#scp root@${HOST_IP}:${KERNEL_SOURCE} /usr/local/ocfs2-test/tmp

# kernel source path in guest node
KERNEL_SOURCE=/usr/local/ocfs2-test/tmp/`basename ${KERNEL_SOURCE}`
sudo chown -R ocfs2test:users ${KERNEL_SOURCE}

for tm in $(echo ${TESTMODE} | sed 's:,: :g'); do
	# try to proceed further when previous one failed
	f_umount

	if [ X"$tm" == X"single" ]; then
		echo -e "\n\n\n"
		f_info "Start single node testing..."

		f_log "single_run-WIP.sh -f 1 -k ${KERNEL_SOURCE} -l /usr/local/ocfs2-test/log -m ${MOUNT_POINT} -d ${SHARED_DISK} ${BLOCKSIZE} ${CLUSTERSIZE} -s ${CLUSTER_STACK} -n ${CLUSTER_NAME} -t ${SINGLE_CASES}"

		single_run-WIP.sh -f 1 -k ${KERNEL_SOURCE} -l /usr/local/ocfs2-test/log -m ${MOUNT_POINT} -d ${SHARED_DISK} ${BLOCKSIZE} ${CLUSTERSIZE}  -s ${CLUSTER_STACK} -n ${CLUSTER_NAME} -t ${SINGLE_CASES}

		f_info "DONE: single node testing"
		continue
	fi

	if [ X"$tm" == X"multiple" ]; then
		echo -e "\n\n\n"
		f_info "Start multiple nodes testing..."

		f_log "multiple_run.sh -f 1 -k ${KERNEL_SOURCE} -n ${NODE_LIST} -d ${SHARED_DISK} ${BLOCKSIZE} ${CLUSTERSIZE}  -s ${CLUSTER_STACK} -C ${CLUSTER_NAME} -t ${MULTIPLE_CASES}  ${MOUNT_POINT}"

		multiple_run.sh -f 1 -k ${KERNEL_SOURCE} -n ${NODE_LIST} -d ${SHARED_DISK} ${BLOCKSIZE} ${CLUSTERSIZE} -t ${MULTIPLE_CASES}  -s ${CLUSTER_STACK} -C ${CLUSTER_NAME}  ${MOUNT_POINT}

		f_info "DONE: multiple nodes testing"
		continue
	fi

	if [ X"$tm" == X"single_discontig_bg" ]; then
		echo -e "\n\n\n"
		f_info "Start single-node discontig block group testing..."

		f_log "discontig_runner.sh -f 1 -d ${SHARED_DISK} ${BLOCKSIZE} ${CLUSTERSIZE}  -s ${CLUSTER_STACK} -n ${CLUSTER_NAME} ${MOUNT_POINT}"

		discontig_runner.sh -f 1 -d ${SHARED_DISK} ${BLOCKSIZE} ${CLUSTERSIZE}  -s ${CLUSTER_STACK} -n ${CLUSTER_NAME} ${MOUNT_POINT}

		f_info "DONE: single-node discontig block group testing"
		continue
	fi

	if [ X"$tm" == X"multiple_discontig_bg" ];then
		echo -e "\n\n\n"
		f_info "Start multiple-node discontig block group testing..."

		f_log "discontig_runner.sh -m ${NODE_LIST} -f 1 -d ${SHARED_DISK} ${BLOCKSIZE} ${CLUSTERSIZE}  -s ${CLUSTER_STACK} -n ${CLUSTER_NAME} ${MOUNT_POINT}"

		discontig_runner.sh -m ${NODE_LIST} -f 1 -d ${SHARED_DISK} ${BLOCKSIZE} ${CLUSTERSIZE}  -s ${CLUSTER_STACK} -n ${CLUSTER_NAME} ${MOUNT_POINT}

		f_info "DONE: multiple-node discontig block group testing"
	fi
done
