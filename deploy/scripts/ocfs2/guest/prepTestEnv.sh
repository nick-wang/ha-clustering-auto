#!/bin/bash
#
# prepTestEnv.sh <MASTER_NODE>
#
# Prepare Env for running ocfs2 test

f_usage()
{
	echo "Usage: `basename ${0}` <MASTER_NODE>"
}

f_info()
{
	echo [INFO]@{`hostname`} $*
}

f_log()
{
	echo [LOG]@{`hostname`} $*
}

if [ $# -lt 1 ];then
	f_usage
	exit 1
fi

# some commands just need to run on anyone of the nodes
MASTER_NODE="$1"

# __MAIN__

# 0. Preparation

# save log messages after reboot
sed -i '/#Storage/a Storage=persistent' /etc/systemd/journald.conf

# 1. My own repo for ocfs2-test has been added, now refresh and install
# ocfs2-test package
f_info "Install ocfs2-test packages"

f_log "zypper --non-interactive refresh"
zypper --non-interactive refresh

f_log "zypper --non-interactive install openmpi ocfs2-test"
zypper --non-interactive install  openmpi
zypper --non-interactive install  ocfs2-test

# it's time to complete the tricky started in sshTestUsr.sh
f_log "chown -R ocfs2test:users /home/ocfs2test/"
chown -R ocfs2test:users /home/ocfs2test/

# 2. Configure dlm RA
f_info "Start pacemaker..."
systemctl start pacemaker.service

f_info "Configure RAs"
if [ x"`hostname`" == x"$MASTER_NODE" ];then
	f_log "\
	crm configure primitive dlm ocf:pacemaker:controld \
		op start interval=0 timeout=90 \
		op stop interval=0 timeout=100 \
		op monitor interval=20 timeout=600"

	crm configure primitive dlm ocf:pacemaker:controld \
		op start interval=0 timeout=90 \
		op stop interval=0 timeout=100 \
		op monitor interval=20 timeout=600

	f_log "crm configure  group base-group dlm"
	crm configure  group base-group dlm

	f_log "crm configure clone base-clone base-group"
	crm configure clone base-clone base-group

	f_log "crm configure show"
	crm configure show

	sleep 3

	f_log "crm status full"
	crm status full
fi

# 3. Make ocfs2test as passwordless sudoer
f_info "Make ocfs2test as passwordless sudoer"
sed -i '/%wheel ALL=(ALL) NOPASSWD: ALL/a ocfs2test ALL=(ALL) NOPASSWD: ALL' /etc/sudoers

# 4. blkid, refer to "man blkid"
sed -i '/^EVALUATE=udev$/ s/$/,scan/' /etc/blkid.conf
