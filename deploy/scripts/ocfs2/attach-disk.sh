#! /bin/bash
function attach_raw_disk()
{
	raw_file=$1
	device_in_guest=$2

	raw_file_size_GB=40

	if [ ! -e $raw_file ]
	then
		dd if=/dev/zero of=$raw_file bs=1G count=$raw_file_size_GB
	fi

	for domain in `cat ${CLUSTER_FILE} | grep HOSTNAME | cut -d"=" -f2`
	do
		virsh attach-disk $domain $raw_file $device_in_guest --live --type disk \
		|| virsh attach-disk $domain $raw_file $device_in_guest  --type disk
		if [ "$?" == "0" ];then
			echo "attach disk [OK]";
		else
			echo "attach disk [FAILED]";
		fi	
	done
	
}



function attach_iscsi()
{
	target_ip=$1
	target=$2
	for ip in `cat ${CLUSTER_FILE} | grep IP_NODE | cut -d'=' -f2`
	do
		config_eth1 $ip
		ssh root@$ip iscsiadm --mode discovery --type sendtargets --portal $target_ip 

		ssh root@$ip iscsiadm --mode node --targetname $target  --portal $target_ip:3260 --login 
	done
}

function config_eth1()
{
	ip=$1
	echo lllllllllllll  $ip
	target_cfg=/etc/sysconfig/network/ifcfg-eth1
	#if [ -z "$(ssh root@$ip ls $target_cfg)" ]
	#then
	scp ./ifcfg-eth1 root@$ip:$target_cfg
	ssh root@$1 rcwicked restart
	#fi
}

function usage()
{
	echo "$0 local \$cluster_file /path/to/raw vdb"
	echo "$0 iscsi \$cluster_file \$target_ip \$target"
}

set -x 
cd "$(dirname "$0")"
disk_from=$1
shift
CLUSTER_FILE=$1
shift
if [ $disk_from = "local" ]
then
	attach_raw_disk "$@"
elif [ $disk_from = "iscsi" ]
then
	attach_iscsi "$@"
fi

