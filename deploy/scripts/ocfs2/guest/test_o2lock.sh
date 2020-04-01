#!/bin/bash
#
# o2locktop CI testing script
#
#set -x

DATE=`which date`
ECHO=`which echo`
TEE=`which tee`
AWK=`which awk`
GREP=`which grep`
PGREP=`which pgrep`
PKILL=`which pkill`
TOUCH=`which touch`
LS=`which ls`
RM=`which rm`
CHMOD=`which chmod`
MOUNT=`which mount`
UMOUNT=`which umount`
MKFS=`which mkfs.ocfs2`

NODE_LIST=${1:-"ghe-tw-nd1,ghe-tw-nd2,ghe-tw-nd3"}
SHARED_DISK=${2:-"/dev/vdb"}
MOUNT_POINT=${3:-"/mnt/ocfs2"}
LOGDIR=/var/lib/ocfs2test
O2LOCKTOPLOG=${LOGDIR}/o2locktop.txt
TESTLOG=${LOGDIR}/test_o2lock.log
LOCALHOST=`${ECHO} ${NODE_LIST} | ${AWK} -F ',' '{print $1}'`
REMOTEHOST=`${ECHO} ${NODE_LIST} | ${AWK} -F ',' '{print $2}'`
NODE_NUM=`${ECHO} ${NODE_LIST} | ${AWK} -F ',' '{print NF}'`

log_message()
{
	${ECHO} "`${DATE}  +\"%F %H:%M:%S\"` $@" | ${TEE} -a ${TESTLOG}
}

log_start()
{
	log_message $@
	START=$(date +%s)
}

log_end()
{
	END=$(date +%s)
	DIFF=$(( ${END} - ${START} ))

	if [ ${1} -ne 0 ]; then
		if [ -z "${2}" ] ; then
			log_message "FAILED (${DIFF} secs)"
		else # test is aborted due to error
			log_message "FAILED (${2})"
			exit 1
		fi
	else
		log_message "PASSED (${DIFF} secs)"
	fi

	START=0
}

log_abort()
{
	log_end 1 "error: $@, aborted!"
}

f_mkfs()
{
	if ${ECHO} "y" | ${MKFS} -N ${NODE_NUM} -F ${SHARED_DISK} >/dev/null 2>&1 ; then
		sync
		sleep 1
		return 0
	else
		log_abort "${MKFS} -N ${NODE_NUM} -F ${SHARED_DISK}"
	fi
}

f_do_on_each_node()
{
	local cmd=$1

	for node in `echo ${NODE_LIST} | sed "s:,: :g"`
	do
		ssh ${node} ${cmd} || return 1
	done

	return 0
}

f_mount()
{
	if f_do_on_each_node "sudo mount ${SHARED_DISK} ${MOUNT_POINT} >/dev/null 2>&1" ; then
		return 0
	else
		log_abort "sudo mount ${SHARED_DISK} ${MOUNT_POINT}"
	fi
}

f_umount()
{
	if f_do_on_each_node "sudo umount ${MOUNT_POINT} >/dev/null 2>&1" ; then
		return 0
	else
		log_abort "sudo umount ${MOUNT_POINT}"
	fi
}

nodename_list()
{
	${ECHO} $1 | ${AWK} -F ',' '{ for (i=1; i<=NF; i++) printf("-n %s ", $i); }'
}

start_o2locktop()
{
	screen -d -m o2locktop `nodename_list ${NODE_LIST}` -l 30 -o ${O2LOCKTOPLOG} ${MOUNT_POINT}
	sleep 1

	if ${PGREP} o2locktop >/dev/null 2>&1 ; then
		return 0
	else
		log_abort "start o2locktop in screen"
	fi
}

stop_o2locktop()
{
	${PKILL} -9 o2locktop
	sleep 1

	if ${PGREP} o2locktop >/dev/null 2>&1 ; then
		log_abort "stop o2locktop with pkill"
		return 1
	else
		return 0
	fi
}

create_file()
{
	if [ "${1}" = "${LOCALHOST}" ] ; then
		${TOUCH} ${2} || log_abort "create ${2} at ${1}"
		${LS} -i ${2} | ${AWK} '{printf "%s", $1}'
	else
		ssh ${1} "${TOUCH} ${2}" || log_abort "create ${2} at ${1}"
		ssh ${1} "${LS} -i ${2}" | ${AWK} '{printf "%s", $1}'
	fi
}

create_multi_files()
{
	for node in `echo ${NODE_LIST} | sed "s:,: :g"`
	do
		create_file ${node} "${1}.${node}"
		echo -n " "
	done

	return 0
}

create_hot_files()
{
	for i in $(seq 1 3)
	do
		create_file ${LOCALHOST} "${1}.${i}"
		echo -n " "
	done
}

create_cold_files()
{
	for i in $(seq 1 100)
	do
		create_file ${LOCALHOST} "${1}.${i}"
		echo -n " "
	done
}

access_file()
{
	local rc=0
	((rc=$RANDOM % 6))

	if [ "${1}" = "${LOCALHOST}" ] ; then
		case $rc in
			1) ${CHMOD} +r ${2} || log_abort "chmod($rc) ${2} at ${1}"
			;;
			2) ${CHMOD} -r ${2} || log_abort "chmod($rc) ${2} at ${1}"
			;;
			3) ${CHMOD} +w ${2} || log_abort "chmod($rc) ${2} at ${1}"
			;;
			4) ${CHMOD} -w ${2} || log_abort "chmod($rc) ${2} at ${1}"
			;;
			5) ${CHMOD} +x ${2} || log_abort "chmod($rc) ${2} at ${1}"
			;;
			*) ${CHMOD} -x ${2} || log_abort "chmod($rc) ${2} at ${1}"
			;;
		esac
	else
		case $rc in
			1) ssh ${1} "${CHMOD} +r ${2}" || log_abort "chmod($rc) ${2} at ${1}"
			;;
			2) ssh ${1} "${CHMOD} -r ${2}" || log_abort "chmod($rc) ${2} at ${1}"
			;;
			3) ssh ${1} "${CHMOD} +w ${2}" || log_abort "chmod($rc) ${2} at ${1}"
			;;
			4) ssh ${1} "${CHMOD} -w ${2}" || log_abort "chmod($rc) ${2} at ${1}"
			;;
			5) ssh ${1} "${CHMOD} +x ${2}" || log_abort "chmod($rc) ${2} at ${1}"
			;;
			*) ssh ${1} "${CHMOD} -x ${2}" || log_abort "chmod($rc) ${2} at ${1}"
			;;
		esac
	fi
}

access_multi_files()
{
	for node in `echo ${NODE_LIST} | sed "s:,: :g"`
	do
		access_file ${node} "${1}.${node}"
	done
}

access_hot_files()
{
	local rc=1

	access_file ${LOCALHOST} "${1}.1"

	((rc=$2 %10))
	if [ $rc -eq 0 ] ; then
		access_file ${LOCALHOST} "${1}.2"
	fi

	((rc=$2 %100))
	if [ $rc -eq 0 ] ; then
		access_file ${LOCALHOST} "${1}.3"
	fi
}

access_cold_files()
{
	local rc=1

	((rc=$2 %1000))
	if [ $rc -eq 0 ] ; then
		for i in $(seq 1 100)
		do
			access_file ${LOCALHOST} "${1}.${i}"
		done
	fi
}

grep_ino_inlog()
{
	if [ -n "$1" ] ; then

		if ${GREP} -A 1 'TYPE INO' ${O2LOCKTOPLOG} | ${GREP} $1 >/dev/null 2>&1 ; then
			return 0
		else
			return 1
		fi

	else

		if ${GREP} -A 1 'TYPE INO' ${O2LOCKTOPLOG} | ${GREP} '[0-9]' >/dev/null 2>&1 ; then
			return 1	# there should not be any active file
		else
			return 0
		fi

	fi
}

grep_inos_inlog()
{
	local inos="$1"
	local num=`${ECHO} ${inos} | ${AWK} -F ' ' '{print NF}'`

	for ino in ${inos[@]}
	do
		if ${GREP} -A ${num} 'TYPE INO' ${O2LOCKTOPLOG} | ${GREP} ${ino} >/dev/null 2>&1 ; then
			:
		else
			return 1
		fi
	done

	return 0
}

grep_inos_inorder()
{
	local inos="$1"
	local num=1

	for ino in ${inos[@]}
	do
		if ${GREP} -A ${num} 'TYPE INO' ${O2LOCKTOPLOG} | ${GREP} ${ino} >/dev/null 2>&1 ; then
			((num++))
		else
			return 1
		fi
	done

	return 0
}

no_file_access()
{
	log_start "no_file_access"

	sleep 30 #do nothing

	grep_ino_inlog
	log_end $?
}

local_file_access()
{
	log_start "local_file_access"
	local fname="${MOUNT_POINT}/localfile"
	local fino=`create_file ${LOCALHOST} ${fname}`

	for i in {1..30}
	do
		access_file ${LOCALHOST} ${fname}
		sleep 1
	done

	grep_ino_inlog ${fino}
	log_end $?
}

remote_file_access()
{
	log_start "remote_file_access"
	local fname="${MOUNT_POINT}/remotefile"
	local fino=`create_file ${REMOTEHOST} ${fname}`

	for i in {1..30}
	do
		access_file ${REMOTEHOST} ${fname}
		sleep 1
	done

	grep_ino_inlog ${fino}
	log_end $?
}

multi_file_access()
{

	log_start "multi_file_access"
	local fname="${MOUNT_POINT}/multifile"
	local finos=`create_multi_files ${fname}`

	for i in {1..30}
	do
		access_multi_files ${fname}
		sleep 1
	done

	grep_inos_inlog "${finos[@]}"
	log_end $?
}

hot_file_access()
{
	log_start "hot_file_access"
	local fname1="${MOUNT_POINT}/hotfile"
	local fname2="${MOUNT_POINT}/coldfile"
	local finos=`create_hot_files ${fname1}`
	create_cold_files ${fname2} >/dev/null 2>&1

	for i in {1..30}
	do
		for k in {1..1000}
		do
			access_hot_files ${fname1} ${k}
			access_cold_files ${fname2} ${k}
		done
		usleep 500000
	done

	grep_inos_inorder "${finos[@]}"
	log_end $?
}

init_fn()
{
	cd ${LOGDIR}
	${RM} -f ${TESTLOG}
	${RM} -f ${O2LOCKTOPLOG}
}

init_test_cases()
{
	log_start "init_test_cases"

	f_mkfs
	f_mount
	start_o2locktop

	log_end 0
}

uninit_test_cases()
{
	log_start "uninit_test_cases"

	stop_o2locktop
	f_umount

	log_end 0
}

run_test_cases()
{
	init_test_cases
	no_file_access
	local_file_access
	remote_file_access
	multi_file_access
	uninit_test_cases
}

# main
init_fn
log_message "*** Start o2locktop (${NODE_LIST} ${SHARED_DISK} ${MOUNT_POINT}) test ***"
run_test_cases
log_message "*** End o2locktop test ***"
