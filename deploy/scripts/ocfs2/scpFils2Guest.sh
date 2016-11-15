#!/bin/bash

f_usage()
{
    echo "scpFils2Guest.sh <--cluster-config=CLUSTER_CONFIG> <SOURCE> <TARGET>"
    echo "	--cluster-config: cluster configuration file"
    echo "	<SOURCE> - source file(s) in host, only support"
    echo "	single directory or file"
    echo "	<TARGET> - Where ocfs2 CTS scripts will be running in guest"
    exit 1
}

if [ $# -ne 3 ]
then
    f_usage
    exit 1
fi

while [ "$#" -gt "0" ]
do
    case "$1" in
	"--cluster-config="*)
	    CLUSTER_CONFIG="${1#--cluster-config=}"
	    ;;
	*)
	    break
	    ;;
    esac
    shift
done

SOURCE="$1"
shift
TARGET="$1"

# Copy files from host to guest
for ip in `cat ${CLUSTER_CONFIG} | grep IP_NODE | cut -d "=" -f 2`
do
{
    echo "ssh root@${ip} [ -d ${TARGET} ] || mkdir ${TARGET}"
    ssh root@${ip} "[ -d ${TARGET} ] || mkdir ${TARGET}"

    if [ -f ${SOURCE} ];then
	echo "scp ${SOURCE} root@${ip}:${TARGET}"
	scp ${SOURCE} root@${ip}:${TARGET}
    else
	echo "scp -r ${SOURCE}/* root@${ip}:${TARGET}"
	scp -r ${SOURCE}/* root@${ip}:${TARGET}
    fi
} &
done
wait
