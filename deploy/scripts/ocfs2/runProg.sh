#!/bin/bash
#
# runProg.sh <--cluster-config=xxx> <--test-config=yyy> [--this-node=zzz] <prog>

f_usage()
{
	echo "Usage: `basename ${0}` <--cluster-config=xxx> <--test-config=yyy> [--this-node=zzz] <prog>"
	echo "	--cluster-config:	cluster configuration file"
	echo "	--test-config:	configuration file to control ocfs2 test"
	echo "	--this-node:	running on the ip-specified node, default to run on all nodes"
	echo "	prog:		program in cluster node"
	exit 1
}

if [ $# -lt "2" ];then
	f_usage
fi

while [ "$#" -gt "0" ]
do
	case "$1" in
	"--cluster-config="*)
		CLUSTER_CONFIG="${1#--cluster-config=}"
		;;
	"--test-config="*)
		TEST_CONFIG="${1#--test-config=}"
		;;
	"--this-node="*)
		THIS_NODE="${1#--this-node=}"
		;;
	*)
		PROGRAM="$1"
	esac
	shift
done

if [ -n "$THIS_NODE" ];then
	echo "ssh root@${THIS_NODE} chown ocfs2test:users ${PROGRAM}"
	ssh root@${THIS_NODE} chown ocfs2test:users ${PROGRAM}

	NODES="`cat ${CLUSTER_CONFIG} | grep NODES | cut -d "=" -f 2`"
	for id in `seq ${NODES}`
	do
		name="`cat ${CLUSTER_CONFIG} | grep HOSTNAME_NODE${id} | cut -d "=" -f 2`"
		if [ ${id} == "1" ];then
			NODE_LIST="${name}"
		else
			NODE_LIST="${NODE_LIST},${name}"
		fi
	done

	echo "ssh root@${THIS_NODE} sudo -u ocfs2test ${PROGRAM} ${TEST_CONFIG} ${NODE_LIST}"
	ssh root@${THIS_NODE} sudo -u ocfs2test ${PROGRAM} ${TEST_CONFIG} ${NODE_LIST}
else
	MASTER_NODE="`cat ${CLUSTER_CONFIG} | grep HOSTNAME_NODE1 | cut -d "=" -f 2`"

	for ip in `cat ${CLUSTER_CONFIG} | grep IP_NODE | cut -d "=" -f 2`
	do
	{
		echo "ssh root@${ip} ${PROGRAM} ${MASTER_NODE}"
		ssh root@${ip} ${PROGRAM} ${MASTER_NODE}
	} &
	done
	wait
fi
