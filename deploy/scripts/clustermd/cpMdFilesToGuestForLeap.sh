#!/bin/bash

function usage()
{
	echo "cpMdFilesToGuestForMilestone.sh <CLUSTER_CONF> 
		<WORKING_DIR_IN_GUEST> <BUILD_LOG_DIR_IN_HOST>"
	exit 2
}

[ $# -ne 3 ] &&
	usage

CLUSTER_CONF=$1
CLUSTERMD_DIR=$2
ips=($(grep IP_NODE $CLUSTER_CONF | cut -d '=' -f2))

for node in ${ips[@]}
do
{	ssh root@${node} "mkdir -p ${CLUSTERMD_DIR}/;\
	mkdir -p ${CLUSTERMD_DIR}/scripts"

	scp ../clustermd/run.sh \
	root@${node}:${CLUSTERMD_DIR}/scripts/
	scp ${CLUSTER_CONF} root@${node}:${CLUSTERMD_DIR}/scripts/
	scp -r ../clustermd/clustermd-autotest root@${node}:/tmp/

	
	ssh $node rpm -qa | grep -q mdadm-[0-9]
	[ $? -eq 0 ] ||
		ssh $node zypper install -y mdadm
	ssh $node rpm -qa | grep -q dlm-kmp-default-[0-9]
	[ $? -eq 0 ] ||
		ssh $node zypper install -y dlm-kmp-default
	ssh $node rpm -qa | grep -q cluster-md-kmp-default-[0-9]
	[ $? -eq 0 ] ||
		ssh $node zypper install -y cluster-md-kmp-default
	ssh $node zypper install -y bc
} &
done
wait

sleep 30

for node in ${ips[@]}
do
	ssh $node "chmod 0600 /root/.ssh/id_rsa;bash ${CLUSTERMD_DIR}/scripts/run.sh"
done

sleep 10
source $CLUSTER_CONF
scp root@${IP_NODE1}:/tmp/clustermd-autotest/tests/test_result $3
scp root@${IP_NODE1}:/tmp/clustermd_test_result.tar.gz $3

exit 0
