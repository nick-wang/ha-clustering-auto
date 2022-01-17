#!/bin/bash
function usage()
{
  echo "$0 <MASTER_CONTAINER_IP:JENKINS_HOST_NAME> <REMOTE_FILE> <LOCAL_FILE>"
  echo -e "\tSet <:JENKINS_HOST_NAME> for container"
  echo -e "eg.\n\t$0 10.67.160.200 /var/tmp/remote_record /var/tmp/local_rec"
  echo -e "or\n\t$0 10.67.160.200:jenkins-ci-host /var/tmp/remote_record /var/tmp/local_rec"
}

if [ $# -ne 3 ]
then
  usage
  exit -1
fi

#Import ENV conf
. functions

case $1 in
	*:*)
		# Run in container
		HOST=${1%:*}
		CONTAINER=${1#*:}
		;;
	*)
		# Directly run on host
		HOST=${1%:*}
		unset CONTAINER
esac

if [ -v CONTAINER ];then
	ssh root@${HOST} "docker exec -t ${CONTAINER} /bin/sh -c \"cat ${2}\"" >${3}
else
	ssh root@${HOST} "cat ${2}" >${3}
fi

# Remove extra ^M(/r) in the result
sed -i "s/\r//g" ${3}

echo "Download the remote file to ${3}"
