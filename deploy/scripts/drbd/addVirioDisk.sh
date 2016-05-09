#!/bin/bash
function usage()
{
  # Better read disk location from yaml file
  # ./addVirioDisk.sh /tmp/jenkins-work/nwang/deploy-cluster-v232/10/cluster_conf 3 /mnt/vm/sles_nick 400M
  echo "addVirioDisk.sh <CLUSTER_CONF_IN_HOST> <HOW_MANY_DISKS_TO_ADD> <DISK_LOCATION> (<DISK_SIZE>)"
  echo "  <HOW_MANY_DISKS_TO_ADD> is limited to 9 disks."
  echo "  Default <DISK_LOCATION> is /mnt/vm, need to use absolute path."
  echo "  Default <DISK_SIZE> is 500M."
  echo "For example:"
  echo "  ./addVirioDisk.sh /tmp/jenkins-work/nwang/deploy-cluster-v232/10/cluster_conf 3 /mnt/vm/sles_nick 400M"
}

if [ $# -lt 2 ] || [ $# -gt 4 ]
then
    usage
    exit -1
fi

#Import ENV conf
. scripts/functions

CLUSTER_CONF=$1
NUM=$2
if [ "x$3" == "x" ]
then
  DIR="/mnt/vm"
else
  DIR=$3
fi

if [ "x$4" == "x" ]
then
  SIZE="500M"
else
  SIZE=$4
fi
#echo $CLUSTER_CONF $NUM $DIR $SIZE

for node in `cat ${CLUSTER_CONF} |grep "HOSTNAME_NODE" |cut -d "=" -f 2`
do
  i=1
  while [ $i -le $NUM ]
  do
    echo "qemu-img create -f raw ${DIR}/${node}-disk${i}.raw $SIZE"
    qemu-img create -f raw ${DIR}/${node}-disk${i}.raw $SIZE
    if [ $? -ne 0 ]
    then
      echo "  Create img Error!"
    fi

    temp=`nconvert ${i}`
    echo "virsh attach-disk ${node} --source ${DIR}/${node}-disk${i}.raw --target vd${temp} --persistent"
    virsh attach-disk ${node} --source ${DIR}/${node}-disk${i}.raw --target vd${temp} --persistent
    if [ $? -ne 0 ]
    then
      echo "  Attach disk error!"
    fi
    i=$((i+1))
  done
done #end for
