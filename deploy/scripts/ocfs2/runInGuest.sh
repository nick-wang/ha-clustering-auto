#!/bin/bash
#
# runInGuest.sh
# 
# Prepare and run ocfs2 CTS	

master_node="ocfs2cts1"
KERNEL_PATH="/mnt/vm/eric"
KERNEL_SOURCE="linux-2.6.39.tar.gz"

f_usage()
{ 
	echo "Usage: `basename ${0}`" 
	exit 1
}

f_info()
{
	echo [INFO]@{`hostname`} $*
}

f_log()
{
	echo [LOG]@{`hostname`} $*
}

# __MAIN__

# 1. My own repo for ocfs2-test has been added, now refresh and install
# ocfs2-test package
f_info "Install ocfs2-test packages"

f_log "zypper --non-interactive refresh"
zypper --non-interactive refresh

f_log "zypper --non-interactive install  ocfs2-test ocfs2-test-debuginfo ocfs2-test-debugsource"
zypper --non-interactive install  ocfs2-test ocfs2-test-debuginfo ocfs2-test-debugsource 

# it's time to complete the tricky
f_log "chown -R ocfs2test:users /home/ocfs2test/.ssh"
chown -R ocfs2test:users /home/ocfs2test/.ssh

# 2. Configure dlm RA
f_info "Configure RAs"
if [ x"`hostname`" == x"$master_node" ];then
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

	sleep 5

	f_log "crm status full"
	crm status full
fi

# 3. Make ocfs2test as passwordless sudoer
f_info "Make ocfs2test as passwordless sudoer"
sed -i '/%wheel ALL=(ALL) NOPASSWD: ALL/a ocfs2test ALL=(ALL) NOPASSWD: ALL' /etc/sudoers

# 4. Create mount point
f_info "Create mount point"
mkdir /mnt/ocfs2
chmod 777 /mnt/ocfs2

# 5. Prepare kernel-source used by ocfs2 CTS
f_info "Prepare kernel-source used by ocfs2 CTS"
f_log "scp root@147.2.207.234:/mnt/vm/eric/linux-2.6.39.tar.gz /usr/local/ocfs2-test/tmp"
scp root@147.2.207.234:${KERNEL_PATH}/${KERNEL_SOURCE} /usr/local/ocfs2-test/tmp
chown -R ocfs2test:users /usr/local/ocfs2-test/tmp/${KERNEL_SOURCE}

# 6. blkid, refer to "man blkid"
sed -i '/^EVALUATE=udev/ s/$/,scan/' /etc/blkid.conf

# 7. Run CTS

# This script should be run by ocfs2test user

f_log "chown ocfs2test:users /var/lib/ocfs2test/runCts.sh"
chown ocfs2test:users /var/lib/ocfs2test/runCts.sh

sudo -u ocfs2test bash << EOF
source ~/.bash_profile

if [ x"`hostname`" == x"ocfs2cts1" ]
then 
	echo "/var/lib/ocfs2test/runCts.sh ..."
	/var/lib/ocfs2test/runCts.sh
fi

EOF
