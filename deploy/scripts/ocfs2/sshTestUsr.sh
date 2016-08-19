#!/bin/bash

# ocfs2-test must be run under non-root account.
# So, passwordless SSH for the test user ("ocfs2test")
# should be setup among nodes.

f_usage()
{
	echo "`basename ${0}` <CLUSTER_CONF>"
	echo "	CLUSTER_CONF:	cluster configuration"
	exit 1
}

if [ $# -ne 1 ]
then
	f_usage
	exit 1
fi

# OCFS2 test account
O2TESTOR=ocfs2test
CLUSTER_CONF=$1

# it's tricky because at this moment we haven't "ocfs2test" user yet. So,
# make home directory for "ocfs2test" in advance, and do
# "chown -R ocfs2test:users /home/ocfs2test/.ssh" later on after test uses
# is created.

echo "======================= Starting of ${0} ============================================"

for ip in `cat ${CLUSTER_CONF} | grep IP_NODE | cut -d "=" -f 2`
do
	echo -n "`basename ${0}` ${1} : configure passwordless ssh for ${O2TESTOR} ....... "
	ssh root@${ip} "mkdir -p /home/${O2TESTOR}/.ssh"
	scp sshkeys/* root@${ip}:/home/${O2TESTOR}/.ssh/
	ssh root@${ip} "chmod 0600 /home/${O2TESTOR}/.ssh/id_rsa"
	cat sshkeys/id_rsa.pub | ssh root@${ip} "cat >> /home/${O2TESTOR}/.ssh/authorized_keys"
	if [ "$?" == "0" ];then
		echo "[OK]";
	else
		echo "[FAILED]";
	fi	
done

echo "======================= End of ${0} =================================================="
