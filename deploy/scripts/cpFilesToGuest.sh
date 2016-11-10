#!/bin/bash
function usage()
{
  echo "cpFilesToGuest.sh <CLUSTER_CONF_IN_HOST> <WORKING_DIR_IN_GUEST> <SKIP_CONFIGURE>"
  echo "Skip configuring cluster if <SKIP_CONGIGURE> is 1"
  exit
}

if [ $# -lt 2 ] || [ $# -gt 3 ]
then
    usage
    exit -1
fi

CLUSTER_CONF=$1
CLUSTER_DIR=$2
SKIP_CLUSTER=${3:-0}

chmod 0600 ../ssh_keys/id_rsa

for ip in `cat ${CLUSTER_CONF} |grep IP_NODE |cut -d "=" -f 2`
do
{
tmp=0
while [ ${tmp} -lt 10 ]
do
    nmap ${ip} 2>&1|grep -q "22/tcp" && echo "${ip} ssh enabled. (${tmp})" && break ||
        tmp=$((tmp+1)) && sleep 3
done

ssh root@${ip} "mkdir -p ${CLUSTER_DIR}/template; mkdir -p ${CLUSTER_DIR}/scripts"

scp ${CLUSTER_CONF} root@${ip}:${CLUSTER_DIR}
scp ../template/*_template root@${ip}:${CLUSTER_DIR}/template/
scp ../template/*_template_1.4.7 root@${ip}:${CLUSTER_DIR}/template/
scp ../template/authkey root@${ip}:${CLUSTER_DIR}/template/
scp -p ../ssh_keys/id_rsa root@${ip}:/root/.ssh/
scp ./configCluster.sh ./functions root@${ip}:${CLUSTER_DIR}/scripts/

if [ ${SKIP_CLUSTER} -ne 1 ]
then
    ssh root@${ip} "cd ${CLUSTER_DIR}; ${CLUSTER_DIR}/scripts/configCluster.sh "
fi
} &
done

wait
