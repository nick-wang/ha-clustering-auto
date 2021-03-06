#########################################################################
# File Name: config_cts.sh
# Author: bin liu
# mail: bliu@suse.com
# Created Time: Tue 15 Sep 2015 09:11:52 AM CST
#########################################################################
#!/bin/bash

#we can get these args by ENV later
. cluster_conf
. cts_conf
. scripts/functions

#get args
node_list=$NODE_LIST
ip_base=$NETADDR
stonith_type="external/$STONITH"
stonith_args=""
#host_ip=$HOST_IP
host_ip=$HOST_IPADDR
node=`hostname`

#remove local node from node list
node_list=`echo ${node_list//','/' '}`
echo $node_list
arr=($node_list)
new_node_list=' '
remote_node_list=' '
for s in ${arr[@]}
do
	if [ $s == $node ];then
		continue
	fi

	if [ "$new_node_list" == ' ' ];then
		new_node_list=$s
		remote_node_list="remote_$s:$s"
	else
	    new_node_list="$new_node_list,$s"
		remote_node_list="$remote_node_list remote_$s:$s"
	fi
done
node_list=`echo ${new_node_list//','/' '}`

sle_ver=($(echo $(getSLEVersion)))
#deal with stonith, external/libvirt, external/sbd and external/ssh so far
#zypper in -y pacemaker-remote
#disable sbd
case ${sle_ver[0]} in
12|42.1|42.2|15)
    systemctl disable sbd
    systemctl enable corosync
    #systemctl disable pacemaker
    systemctl stop pacemaker
    systemctl start pacemaker
    zypper in -y pacemaker-cts
    ;;
11)
    chkconfig sbd off
    #chkconfig openais off
    service openais stop
    service openais start
    zypper in -y libpacemaker-devel
    ;;
*)
    echo "Not support. SLE${sle_ver[0]} SP${sle_ver[1]}"
esac

if [ $stonith_type == "external/libvirt" ];then
    zypper in -y libvirt
    #stonith_args="--stonith-args hypervisor_uri='qemu+tcp://$host_ip/system',hostlist='$node_list $remote_node_list'"
    stonith_args="--stonith-args hypervisor_uri='qemu+tcp://$host_ip/system',hostlist='$node_list'"
elif [ $stonith_type == "external/sbd" ];
then
	stonith_args=""
fi

#form the commandline
new_node_list=`echo ${new_node_list//','/' '}`

#filter unnecessary message "Script /var/lib/pacemaker/notify.sh does not exist"
#"Value '/var/lib/pacemaker/notify.sh' for cluster option 'notification-agent' is invalid.  Defaulting to /dev/null"
echo "exit 0" > /var/lib/pacemaker/notify.sh
chmod +x /var/lib/pacemaker/notify.sh
#update cprpsync and pacemaker
zypper up -y pacemaker libpacemaker3 pacemaker-cli pacemaker-cts corosync

isMaster "$HOSTNAME_NODE1"
if [ $? -ne 0 ]
then
    exit 0
fi

case ${sle_ver[0]} in
  12|42.1|42.2|15)
    systemctl stop pacemaker
    ;;
  11)
    service openais stop
    ;;
  *)
    echo "Not support. SLE${sle_ver[0]} SP${sle_ver[1]}"
esac
#a=`echo $ip_base|awk -F . {'print $1'}`
#b=`echo $ip_base|awk -F . {'print $2'}`
#c=`echo $ip_base|awk -F . {'print $3'}`
#ip_base="$a.$b.$c.220"
#echo "/usr/share/pacemaker/tests/cts/CTSlab.py --nodes '$new_node_list' --outputfile pacemaker.log --populate-resources --test-ip-base $ip_base --stonith 1 --stack corosync --stonith-type $stonith_type $stonith_args"  > run_cts.sh
echo "/usr/share/pacemaker/tests/cts/CTSlab.py --nodes '$new_node_list' --outputfile pacemaker.log --clobber-cib --stonith 1 --once --stack corosync --stonith-type $stonith_type $stonith_args 1"
echo "/usr/share/pacemaker/tests/cts/CTSlab.py --nodes '$new_node_list' --outputfile pacemaker.log --clobber-cib --stonith 1 --once --stack corosync --stonith-type $stonith_type $stonith_args 1"  > run_cts.sh
bash run_cts.sh
