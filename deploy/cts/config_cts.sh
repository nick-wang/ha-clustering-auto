#########################################################################
# File Name: config_cts.sh
# Author: bin liu
# mail: bliu@suse.com
# Created Time: Tue 15 Sep 2015 09:11:52 AM CST
#########################################################################
#!/bin/bash
rpm -qa|grep -w pacemaker-cts
installed = $?
if [ $installed -ne 0 ]; then
	rpm -ivh pacemaker-cts*
fi

rpm -qa|grep -w corosync-testagents
installed = $?
if [ $installed -ne 0 ]; then
	rpm -ivh corosync-testagents*
fi
