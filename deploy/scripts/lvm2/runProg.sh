#!/bin/bash
#
# runProg.sh <--cluster-config=xxx> <--test-config=yyy> [--this-node=zzz] <prog>

THIS_NODE=""

f_usage()
{
	echo "Usage: `basename $0` <--cluster-config=xxx> [--test-config=yyy] [--this-node=zzz] <prog>"
	echo "	--cluster-config:	cluster configuration file"
	echo "	--test-config:	configuration file to control the testing"
	echo "	--this-node:	running on the ip-specified node, default to run on all nodes"
	echo "	prog:	program in cluster node"
}

if [ $# -lt 2 ] ; then
	f_usage
	exit 1
fi

while [ $# -gt 0 ]
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

. "$CLUSTER_CONFIG"

if [ -n "$THIS_NODE" ] ; then
	# only run on this node
	echo "ssh root@${THIS_NODE} ${PROGRAM} ${TEST_CONFIG}"
	ssh root@${THIS_NODE} ${PROGRAM} ${TEST_CONFIG}
else
	# Sometime, we need to give master node special treat
	MASTER_NODE="$HOSTNAME_NODE1"

	for i in `seq "$NODES"`
	do
	{
		eval ip='$'IP_NODE$i
		echo "ssh root@${ip} ${PROGRAM} ${MASTER_NODE}"
		ssh root@${ip} ${PROGRAM} ${MASTER_NODE}
	} &
	done

	wait
fi
