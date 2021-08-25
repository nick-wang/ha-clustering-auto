#!/bin/bash

#Configure machines list first
################
NODES=(192.168.122.57 192.168.122.29 192.168.122.35 192.168.122.216)
RANDOM_FILES=30
################

function usage()
{
  echo -e "Usage:\n\t$0 <DRBD_RES_NAME> <RUN_TIMES> (<OUTPUT_DIR>) (<CLUSTER_CONF>)"
}

if [ $# -lt 2 ] || [ $# -gt 4 ]
then
  usage
  exit -1
fi

RES_NAME=$1
RUN_TIMES=$2
OUTPUT_DIR=${3-"./"}
CLUSTER_CONF=${4}

$(which bc >/dev/null 2>&1)
if [ $? != 0 ];then
	$(zypper --non-interactive install bc)
    if [ $? != 0 ];then
	  echo "Package/binary bc not installed, quit testing."
	  exit -1
	fi
fi

if [ ! -z $CLUSTER_CONF ] && [ -e $CLUSTER_CONF ];then
  ips=$(cat ${CLUSTER_CONF} |grep "^IP_NODE"|cut -d "=" -f 2|xargs)
  NODES=(${ips})
fi

OUTPUT=${OUTPUT_DIR}/drbdMD5sum-result

function pickOneRandomNumber()
{
  a=$(echo "$RANDOM%${#NODES[@]}" | bc)
  echo $a
}

function verifyIt()
{
  echo -n "=== Verify(${1}):"
  ssh root@${1} "echo \" on \$HOSTNAME\""
  ssh root@${1} "drbdadm primary ${2}"
  minor=$(ssh root@${1} "drbdsetup status ${2} --verbose |grep minor|sed 's/.* minor:\([0-9]*\).*/\1/'")
  ssh root@${1} "mount /dev/drbd${minor} /mnt; cd /mnt;
                 md5sum -c md5file"
  ssh root@${1} "umount /mnt; sleep 2; drbdadm secondary ${2}"
}

function testIt()
{
  echo -n "=== Make it primary(${1}):"
  ssh root@${1} "echo \" on \$HOSTNAME\""
  ssh root@${1} "drbdadm primary ${2}"
  echo "=== Generate random files:"
  minor=$(ssh root@${1} "drbdsetup status ${2} --verbose |grep minor|sed 's/.* minor:\([0-9]*\).*/\1/'")
  ssh root@${1} "mount /dev/drbd${minor} /mnt; cd /mnt;
                 for i in \$(seq ${RANDOM_FILES}); do dd if=/dev/random of=./myrandom.file\${i} bs=512 count=20000 >/dev/null 2>&1; sleep 1; done;
                 rm -rf md5file; for i in \$(ls myrandom.file*); do md5sum \${i} >> md5file; done; cat md5file"
  sleep 5;
  ssh root@${1} "cd /; umount /mnt; sleep 2; drbdadm secondary ${2}"
}

function checkResult()
{
  for line in $(cat ${OUTPUT}|grep "^myrandom.file"|cut -d ":" -f 2)
  do
    $(echo ${line}|grep "OK" >/dev/null)
	if [ $? != 0 ];then
	  echo "Failed to verify the MD5sum."
	  cat ${OUTPUT}
	  exit -2
	fi
  done
}

rm -rf ${OUTPUT}
for i in `seq ${RUN_TIMES}`
do
  randomNo=$(pickOneRandomNumber)
  ip=${NODES[${randomNo}]}
  testIt $ip $RES_NAME

  randomNo=$(pickOneRandomNumber)
  ip=${NODES[${randomNo}]}
  verifyIt $ip $RES_NAME | tee -a ${OUTPUT}
done
