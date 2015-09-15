#########################################################################
# File Name: run_cts.sh
# Author: bin liu
# mail: bliu@suse.com
# Created Time: Tue 15 Sep 2015 09:22:31 AM CST
#########################################################################
#!/bin/bash

#run stack of openais
/usr/share/pacemaker/tests/cts/CTSlab.py --nodes $node_list --outputfile my.log --populate-resources --test-ip-base $IP_BASE --stonith ssh --stack openais

#run stack of corosync
/usr/share/pacemaker/tests/cts/CTSlab.py --nodes $node_list --outputfile my.log --populate-resources --test-ip-base $IP_BASE --stonith ssh --stack corosync

#run corosync test suit, this is not in rpm, but only in source code, shall we run this test?
#cd $COROSYNC_DIR
#cp /etc/corosync/corosync.conf conf/corosync.example
#./corolab.py --nodes $node_list
