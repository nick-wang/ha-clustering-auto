#!/bin/bash
function usage()
{
  echo "shutdownCluster.sh <CLUSTER_CONF_IN_HOST>"
  echo "Skip configuring cluster if <SKIP_CONGIGURE> is 1"
  exit
}

if [ $# -ne 1 ]
then
    usage
    exit -1
fi

CLUSTER_CONF=$1


for ip in `cat ${CLUSTER_CONF} |grep IP_NODE |cut -d "=" -f 2`
do
{
ssh root@${ip} "shutdown -h 0"
} &
done

wait
