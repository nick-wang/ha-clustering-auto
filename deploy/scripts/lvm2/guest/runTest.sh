#!/bin/bash
#
# runTest.sh   <TEST_CONF>
#
# Launch testing

HOSTNAME=`hostname`

f_usage()
{
	echo "Usage: `basename $0` <TEST_CONF>"
	exit 1
}

f_info()
{
	echo [INFO]@${HOSTNAME} $*
}

f_log()
{
	echo [LOG]@${HOSTNAME} $*
}

if [ $# -ne 1 ];then
	f_usage
	exit 1
fi

TEST_CONF="$1"

f_info "Dump testing configuration for lvm2 test:"
cat ${TEST_CONF}

HOST_IP="`cat ${TEST_CONF} | grep HOST_IP | cut -d "=" -f 2`"

# __MAIN__

# redirect testing runner output to logfile
/usr/share/qa/tools/test_lvm2_2_02_120-run | tee /tmp/test_lvm2_2_02_120-run.log
