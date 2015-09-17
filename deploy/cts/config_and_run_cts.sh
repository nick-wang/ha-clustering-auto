#########################################################################
# File Name: config_cts.sh
# Author: bin liu
# mail: bliu@suse.com
# Created Time: Tue 15 Sep 2015 09:11:52 AM CST
#########################################################################
#!/bin/bash

zypper in -y pacemaker-cts

#we can get these args by ENV later
. cluster_conf

#get args
node_list=$1
ip_base=$2
stonith_type=$3
stonith_args=""
host_ip=$4
node=`hostname`

#remove local node from node list
node_list=`echo ${node_list//','/' '}`
echo $node_list
arr=($node_list)
new_node_list=' '
for s in ${arr[@]}
do
	if [ $s == $node ];then
		continue
	fi

	if [ "$new_node_list" == ' ' ];then
		new_node_list=$s
	else
	    new_node_list="$new_node_list,$s"
	fi
done
node_list=`echo ${new_node_list//','/' '}`

#deal with stonith, external/libvirt, external/sbd and external/ssh so far
if [ $stonith_type == "external/libvirt" ]
then
	zypper in -y libvirt
    stonith_args="--stonith_args hypervisor_uri='qemu+tcp://$host_ip/system',hostlist='$node_list'"
elif [ $stonith_type == "external/sbd" ]
then
	stonith_args="--stonith_args SBD_DEVICE='/dev/disk/by-path/ip-$TARGET_IP:3260-iscsi-$(TARGET_LUN)-lun-0',SBD_OPTS='-W'"
fi

#form the commandline
echo "/usr/share/pacemaker/tests/cts/CTSlab.py --nodes $new_node_list --outputfile my.log --populate-resources --test-ip-base $ip_base --stonith 1 --stack corosync --stonith_type $stonith_type $stonith_args"
