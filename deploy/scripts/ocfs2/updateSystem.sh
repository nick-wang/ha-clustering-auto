#!/bin/bash

f_usage()
{
    echo "`basename ${0}` --cluster-config=<cluser configuration>"
}

# main
if [ $# -ne 1 ];then
    f_usage
    exit 1
fi

while [ $# -gt "0" ]
do
    case "$1" in
	"--cluster-config="*)
	    CLUSTER_CONFIG="${1#--cluster-config=}"
	    ;;
    esac

    shift
done

NUM_NODES="`cat ${CLUSTER_CONFIG} | grep NODES | cut -d'=' -f2`"
for id in `seq ${NUM_NODES}`
do
{
	ip="`cat ${CLUSTER_CONFIG} | grep IP_NODE${id} | cut -d "=" -f 2`"
	name="`cat ${CLUSTER_CONFIG} | grep HOSTNAME_NODE${id} | cut -d "=" -f 2`"

        echo "ssh root@${ip} zypper --non-interactive install ocfs2-tools"
        ssh root@${ip} "zypper --non-interactive install ocfs2-tools"

        echo "ssh root@${ip} zypper --non-interactive install libdlm"
        ssh root@${ip} "zypper --non-interactive install libdlm"

	# openSUSE doesn't release KMPs, maybe ugly, but no harm
        echo "ssh root@${ip} zypper --non-interactive install ocfs2-kmp-default"
        ssh root@${ip} "zypper --non-interactive install ocfs2-kmp-default"

        echo "ssh root@${ip} zypper --non-interactive install dlm-kmp-default"
        ssh root@${ip} "zypper --non-interactive install dlm-kmp-default"

	echo "ssh root@${ip} zypper --non-interactive install kernel-default"
	ssh root@${ip} "zypper --non-interactive install kernel-default"

	# reboot
	echo virsh reset ${name}
	virsh reset ${name}

	sleep 3

	# wait for booting up
	count=6
	timeout=30
	sleeptime=10
	while [ "$count" -gt "0" ]; do
	    echo ssh -o ConnectTimeout=${timeout} root@${ip} "true"
	    ssh -o ConnectTimeout=${timeout} root@${ip} "true"
	    if [ $? == "0" ];then
		echo "SUCESS: got connection to ${name}:${ip}"
		break;
	    fi
	    sleep ${sleeptime}
	    count=$((count-1))
	done

	if [ "$count" -eq "0" ]; then
	    echo "ERROR: giving up ping ${ip} after retrying several times"
	    exit 1
	fi
} &
done
wait
