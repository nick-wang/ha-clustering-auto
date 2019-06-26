#!/bin/bash

function usage()
{
	echo "cpMdFilesToGuestForMilestone.sh <CLUSTER_CONF> <BUILD_LOG_DIR_IN_HOST>"
	exit 2
}

[ $# -ne 2 ] && usage

CLUSTER_CONF=$1
ips=($(grep IP_NODE $CLUSTER_CONF | cut -d '=' -f2))

cp -f $CLUSTER_CONF ./clustermd/clustermd-autotest/clustermd_tests/

for node in ${ips[@]}
do
{
	pkgs=(mdadm dlm-kmp-default cluster-md-kmp-default )
	for pkg in ${pkgs[@]}
	do
		ssh $node rpm -qa | grep -q $pkg
		[ $? -eq 0 ] ||
			ssh $node zypper install -y $pkg
	done
	ssh $node "modprobe dlm"
	ssh $node "rcpacemaker restart"
} &
done
wait
sleep 10

node=$(grep IP_NODE1 $CLUSTER_CONF | cut -d '=' -f2)
scp clustermd/run.sh root@$node:/tmp
scp -r clustermd/clustermd-autotest root@$node:/tmp/

ssh root@$node "chmod 0600 /root/.ssh/id_rsa; bash /tmp/run.sh"

sleep 1
scp root@$node:/root/tt/result $2
scp root@$node:/root/test_result.tar.gz $2

exit 0
