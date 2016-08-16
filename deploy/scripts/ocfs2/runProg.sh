#!/bin/bash
#
# runProg.sh <--cluster-conf> <--cts-conf> [--this-node] <prog>

f_usage()
{
	echo "Usage: `basename ${0}` <--cluster-conf> <--cts-conf> [--this-node] <script>"
	echo "	--cluster-conf:	cluster configuration file"
	echo "	--cts-conf:	configuration file to control ocfs2 test"
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
	"--cluster-conf="*)
		CLUSTER_CONF="${1#--cluster-conf=}"
		;;
	"--cts-conf="*)
		CTS_CONF="${1#--cts-conf=}"
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

	NODES="`cat $CLUSTER_CONF |grep NODES |cut -d "=" -f 2`"
	for id in `seq ${NODES}`
	do
		name="`cat $CLUSTER_CONF |grep HOSTNAME_NODE${id} |cut -d "=" -f 2`"
		if [ ${id} == "1" ];then
			NODE_LIST="${name}"
		else
			NODE_LIST="${NODE_LIST},${name}"
		fi
	done

	echo "ssh root@${THIS_NODE} sudo -u ocfs2test ${PROGRAM} ${CTS_CONF} ${NODE_LIST}"
	ssh root@${THIS_NODE} sudo -u ocfs2test ${PROGRAM} ${CTS_CONF} ${NODE_LIST}
else
	MASTER_NODE="`cat $CLUSTER_CONF |grep HOSTNAME_NODE1 |cut -d "=" -f 2`"

	for ip in `cat $CLUSTER_CONF |grep IP_NODE |cut -d "=" -f 2`
	do
	{
		echo "ssh root@${ip} ${PROGRAM} ${MASTER_NODE}"
		ssh root@${ip} ${PROGRAM} ${MASTER_NODE}
	} &
	done
	wait
fi
