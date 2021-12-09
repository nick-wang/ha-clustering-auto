#!/bin/bash

if [ ! -d "/etc/dlm" ];then
	mkdir /etc/dlm
fi
if [ ! -d "/etc/lvm" ];then
	mkdir /run/lvm
fi

bkup_dir=`pwd`
# do special patch for 2 nodes cluster env
cd /usr/share/lvm2-testsuite/shell/
cp aa-lvmlockd-dlm-prepare.sh aa-lvmlockd-dlm-prepare.sh.pre
cp zz-lvmlockd-dlm-remove.sh zz-lvmlockd-dlm-remove.sh.pre

old="lvmlockctl --stop-lockspaces"
new="lvmlockctl -i\n\
for i in \`lvmlockctl -i | grep \"VG LVM.*vg lock_type=dlm\" | cut -d \' \' -f 2\`; do\n\
    echo \" ===> call lvmlockctl --drop \$i\"\n\
    lvmlockctl --drop \$i\n\
done\n\n\
lvmlockctl --stop-lockspaces"
sed -i "s/$old/$new/g" zz-lvmlockd-dlm-remove.sh

sed -i "s/aux prepare_dlm/#aux prepare_dlm/g" aa-lvmlockd-dlm-prepare.sh
sed -i "s/systemctl stop dlm/#systemctl stop dlm/g" zz-lvmlockd-dlm-remove.sh
sed -i "s/systemctl stop corosync/#systemctl stop corosync/g" zz-lvmlockd-dlm-remove.sh
cd ${bkup_dir}


# below part copy from ocf2: Configure dlm RA
echo "Start pacemaker..."
systemctl start pacemaker.service

# some commands just need to run on anyone of the nodes
MASTER_NODE="$1"
echo "hostname: `hostname`"
echo "master_node: ${MASTER_NODE}"
echo "Configure RAs"
if [ x"`hostname`" == x"$MASTER_NODE" ];then
	echo "\
	crm configure primitive dlm ocf:pacemaker:controld \
		op start interval=0 timeout=90 \
		op stop interval=0 timeout=100 \
		op monitor interval=20 timeout=600"

	crm configure primitive dlm ocf:pacemaker:controld \
		op start interval=0 timeout=90 \
		op stop interval=0 timeout=100 \
		op monitor interval=20 timeout=600

	echo "crm configure  group base-group dlm"
	crm configure  group base-group dlm

	echo "crm configure clone base-clone base-group"
	crm configure clone base-clone base-group

	echo "crm configure show"
	crm configure show

	sleep 3

	echo "crm status full"
	crm status full
fi

# remove previous complete file.
rm -f complete.txt

# grasp ramdisk which will make lvm2-testsuit use loop devices.
modprobe brd rd_nr=1 rd_size=1

echo "current pwd: `pwd`"
echo "create start file"
echo `date +%Y%m%d-%H%M` > start.txt

# quick verify env
#lvm2-testsuite --flavours udev-lvmlockd-dlm --only shell/aa-lvmlockd-dlm-prepare.sh,shell/activate-minor.sh,shell/covercmd.sh,shell/zz-lvmlockd-dlm-remove.sh
#sleep 2

# start test.  "S=": skip test cases
# NOTE: above (included) "shell/thin-large.sh cases are must skip cases.
S="\
shell/autoactivation-metadata.sh,\
shell/dmeventd-restart.sh,\
shell/lvchange-raid.sh,\
shell/lvchange-raid1-writemostly.sh,\
shell/lvchange-raid10.sh,\
shell/lvchange-raid456.sh,\
shell/lvconvert-cache-abort.sh,\
shell/lvconvert-raid-allocation.sh,\
shell/lvconvert-raid-reshape-striped_to_linear.sh,\
shell/lvconvert-raid-reshape.sh,\
shell/lvconvert-raid-takeover.sh,\
shell/lvconvert-raid.sh,\
shell/lvconvert-repair-mirror.sh,\
shell/lvconvert-raid1-split-trackchanges.sh,\
shell/lvconvert-raid456.sh,\
shell/lvcreate-large-raid.sh,\
shell/lvconvert-cache-abort.sh,\
shell/lvconvert-raid-allocation.sh,\
shell/lvconvert-raid-restripe-linear.sh,\
shell/lvconvert-raid-reshape-striped_to_linear-single-type.sh,\
shell/lvextend-snapshot-dmeventd.sh,\
shell/snapshot-merge.sh,\
shell/snapshot-merge-stack.sh,\
shell/process-each-duplicate-pvs.sh,\
shell/pvmove-restart.sh,\
shell/thin-flags.sh,\
shell/thin-large.sh,\
shell/component-thin.sh,\
shell/inconsistent-metadata.sh,\
shell/lvchange-rebuild-raid.sh,\
shell/lvchange-syncaction-raid.sh,\
shell/lvextend-snapshot-dmeventd.sh,\
shell/lvconvert-mirror.sh,\
shell/lvconvert-raid10.sh,\
shell/lvconvert-raid-takeover-raid4_to_linear.sh,\
shell/lvconvert-snapshot-raid.sh,\
shell/lvcreate-repair.sh,\
shell/lvm-on-md.sh,\
shell/lvresize-raid.sh,\
shell/lvcreate-thin.sh,\ 
shell/lvcreate-raid.sh,\
shell/lvconvert-repair-raid.sh,\
shell/lvconvert-raid-takeover-thin.sh,\
shell/lvconvert-mirror.sh,\
shell/lvconvert-mirror-basic-0.sh,\
shell/lvconvert-mirror-basic-1.sh,\ 
shell/lvconvert-mirror-basic-2.sh,\
shell/lvconvert-thin-raid.sh,\
shell/lvconvert-raid10.sh,\
shell/lvconvert-raid-takeover-thin.sh,\
shell/lvconvert-raid-takeover-raid4_to_linear.sh,\
shell/lvconvert-raid-reshape-stripes-load-reload.sh,\
shell/lvconvert-cache-raid.sh,\ 
shell/lvm-on-md.sh,\
shell/metadata-balance.sh,\
shell/missing-pv-unused.sh,\
shell/nomda-missing.sh,\
shell/pvcreate-operation.sh,\
shell/pvremove-thin.sh,\
shell/pvmove-cache-segtypes.sh,\
shell/pvmove-resume-2.sh,\
shell/pvck-dump.sh,\
shell/pvcreate-usage.sh,\
shell/process-each-vg.sh,\
shell/process-each-lv.sh,\
shell/thin-foreign-dmeventd.sh,\
shell/thin-dmeventd-warns.sh,\
shell/unknown-segment.sh,\
shell/vgcreate-usage.sh,\
shell/vgchange-many.sh,\
shell/vgextend-usage.sh" \
lvm2-testsuite --flavours udev-lvmlockd-dlm

# create complete file, jenkins will check this file.
echo "create complete file"
echo `date +%Y%m%d-%H%M` > complete.txt

exit 0
