#!/bin/bash
#
# prepTestEnv.sh <MASTER_NODE>
#
# Prepare Env for running ocfs2 test

HOSTNAME=`hostname`

f_usage()
{
	echo "Usage: `basename $0` <MASTER_NODE>"
}

f_info()
{
	echo [INFO]@"$HOSTNAME" $*
}

f_log()
{
	echo [LOG]@"$HOSTNAME" $*
}

if [ $# -lt 1 ];then
	f_usage
	exit 1
fi

# A master node is a node with the lowest id by default.
# We need to do something specifal on it sometimes.
MASTER_NODE="$1"

# __MAIN__

# 0. Preparation

# save log messages after reboot
sed -i '/#Storage/a Storage=persistent' /etc/systemd/journald.conf

# 1. We've added QA repo. Now, refresh and intall qa_test_lvm2

f_info "Install qa_test_lvm2 packages"

f_log "zypper --gpg-auto-import-keys refresh"
zypper --gpg-auto-import-keys refresh

f_log "zypper --non-interactive install qa_test_lvm2"
zypper --non-interactive install qa_test_lvm2
