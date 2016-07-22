#!/bin/bash
#
# runCts.sh
# 
# Run ocfs2 CTS	

f_usage()
{ 
	echo "Usage: `basename ${0}`" 
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

echo -e "\n\n\n"
f_info "Start single node testing..."

BLOCKSIZE=4096
CLUSTERSIZE=32768
testcases="create_and_open,directaio,fillverifyholes,renamewriterace,mmaptruncate,aiostress,filesizelimits,buildkernel,splice,sendfile,mmap,inline,xattr,mkfs,tunefs,backup_super,reflink"

f_umount()
{
	dev=`mount -t ocfs2`

	if [ -n "$dev" ];then
		f_log "sudo umount /mnt/ocfs2"
		sudo umount /mnt/ocfs2
	fi
}

f_log "single_run-WIP.sh -k /usr/local/ocfs2-test/tmp/linux-2.6.39.tar.gz -l /usr/local/ocfs2-test/log -m /mnt/ocfs2/ -d /dev/disk/by-path/ip-147.2.207.237:3260-iscsi-eric.2015-12.suse.bej:ocfs2-san2-lun-0 -b ${BLOCKSIZE} -c ${CLUSTERSIZE} -t ${testcases}"

single_run-WIP.sh -k  /usr/local/ocfs2-test/tmp/linux-2.6.39.tar.gz -l /usr/local/ocfs2-test/log -m /mnt/ocfs2/ -d /dev/disk/by-path/ip-147.2.207.237:3260-iscsi-eric.2015-12.suse.bej:ocfs2-san2-lun-0 -b ${BLOCKSIZE} -c ${CLUSTERSIZE} -t ${testcases} &	

wait
f_info "DONE: single node testing"
f_umount

sleep 3

echo -e "\n\n\n"
f_info "Start multiple nodes testing..."

testcases="xattr,inline,reflink,write_append_truncate,multi_mmap,create_racer,flock_unit,cross_delete,open_delete,lvb_torture"

f_log "multiple_run.sh -k /usr/local/ocfs2-test/tmp/linux-2.6.39.tar.gz -n ocfs2cts1,ocfs2cts2 -d /dev/disk/by-path/ip-147.2.207.237:3260-iscsi-eric.2015-12.suse.bej:ocfs2-san2-lun-0 -b ${BLOCKSIZE} -c ${CLUSTERSIZE} -t ${testcases}  /mnt/ocfs2"

multiple_run.sh -k /usr/local/ocfs2-test/tmp/linux-2.6.39.tar.gz -n ocfs2cts1,ocfs2cts2 -d /dev/disk/by-path/ip-147.2.207.237:3260-iscsi-eric.2015-12.suse.bej:ocfs2-san2-lun-0 -b ${BLOCKSIZE} -c ${CLUSTERSIZE} -t ${testcases} /mnt/ocfs2 &

wait

f_info "DONE: multiple nodes testing"
