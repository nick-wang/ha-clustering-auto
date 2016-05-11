#!/bin/bash
function usage()
{
  echo "cpFilesToGuest.sh <CLUSTER_CONF_IN_HOST> <WORKING_DIR_IN_GUEST>"
  exit
}

if [ $# -ne 2 ]
then
    usage
    exit -1
fi

CLUSTER_CONF=$1
CLUSTER_DIR=$2

chmod 0600 ../ssh_keys/id_rsa

for ip in `cat ${CLUSTER_CONF} |grep IP_NODE |cut -d "=" -f 2`
do
{
ssh root@${ip} "mkdir -p ${CLUSTER_DIR}/template; mkdir -p ${CLUSTER_DIR}/scripts"

scp ${CLUSTER_CONF} root@${ip}:${CLUSTER_DIR}
scp ../template/*_template root@${ip}:${CLUSTER_DIR}/template/
scp ../template/*_template_1.4.7 root@${ip}:${CLUSTER_DIR}/template/
scp ../template/authkey root@${ip}:${CLUSTER_DIR}/template/
scp -p ../ssh_keys/id_rsa root@${ip}:/root/.ssh/
scp ./configCluster.sh ./functions root@${ip}:${CLUSTER_DIR}/scripts/

ssh root@${ip} "cd ${CLUSTER_DIR}; ${CLUSTER_DIR}/scripts/configCluster.sh "
} &
done

wait
