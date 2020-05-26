#!/bin/bash

# remove previous complete file.
rm -f complete.txt

# grasp ramdisk which will make lvm2-testsuit use loop devices.
modprobe brd rd_nr=1 rd_size=1

# quick verify env
#T=pvcreate-ff.sh lvm2-testsuite

# start test. S: skip test cases. (these cases may make testing hung or forever failed)
S="\
api/dbustest.sh,\
shell/aa-lvmlockd-dlm-prepare.sh,\
shell/aa-lvmlockd-sanlock-prepare.sh,\
shell/lvmlockd-hello-world.sh,\
shell/lvmlockd-lv-types.sh,\
shell/clvmd-restart.sh,\
shell/zz-lvmlockd-dlm-remove.sh,\
shell/zz-lvmlockd-sanlock-remove.sh,\
shell/lvchange-vdo.sh,\
shell/lvconvert-cache-vdo.sh,\
shell/lvconvert-vdo.sh,\
shell/lvcreate-vdo-cache.sh,\
shell/lvcreate-vdo.sh,\
shell/lvextend-vdo-dmeventd.sh,\
shell/lvextend-vdo.sh,\
shell/lvresize-vdo.sh,\
shell/profiles-vdo.sh,\
shell/vdo-autoumount-dmeventd.sh,\
shell/dmeventd-restart.sh,\
shell/lvchange-raid10.sh,\
shell/lvchange-raid1-writemostly.sh,\
shell/lvchange-raid456.sh,\
shell/lvconvert-repair-mirror.sh,\
shell/lvconvert-raid1-split-trackchanges.sh,\
shell/lvcreate-large-raid.sh,\
shell/lvconvert-cache-abort.sh,\
shell/lvconvert-raid-allocation.sh,\
shell/lvconvert-raid-restripe-linear.sh,\
shell/lvconvert-raid-reshape-striped_to_linear-single-type.sh,\
shell/lvextend-snapshot-dmeventd.sh,\
shell/snapshot-merge-stack.sh,\
shell/thin-flags.sh,\
shell/thin-large.sh" \
lvm2-testsuite --flavours ndev-vanilla

# create complete file, jenkins will check this file.
echo "create complete file"
echo `date +%Y%m%d-%H%M` > complete.txt

exit 0
