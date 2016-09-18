#!/bin/bash

function usage()
{
  echo "create_target.sh -i <ISCSI_BLOCK_NAME> -v <VOLUME_GROUP> -n <NET_CARD>"
  echo "  args: [-i, -v, -n ] [--iblock=, --vg=, --net=]"
  echo "  example: create_target.sh -i <iblock> -v <volumegroup> (-n <netcard>)"
}

opt_name=""
opt_vg=""
opt_net=""

GETOPT_ARGS=`getopt -o i:v:n: -al iblock:,vg:,net: -- "$@"`
eval set -- "$GETOPT_ARGS"

while [ -n "$1" ]
do
	case "$1" in
		-i|--iblock) opt_name=$2; shift 2;;
		-v|--vg) opt_vg=$2; shift 2;;
		-n|--net) opt_net=$2; shift 2;;
		--) break ;;
	esac
done

if [ -z $opt_name ] || [ -z $opt_vg ]
then 
   usage
   exit -1
fi

iblock_name=${opt_name}
vgname=${opt_vg}
net=${opt_net:="eth0"}


# ---- modify below if necessary ----
# Automatica calc ipaddr of netcard
# ip a | grep -A 2 " eth0:" |sed -n "s/.*inet \(.*\)\/.*/\1/p"
portals_ip=`ip a | grep -A 2 " ${net}:" |sed -n "s/.*inet \(.*\)\/.*/\1/p"`
# ---- modify above if necessary ----

year=`date +%y`
month=`date +%m`
target_name="iqn.20${year}-${month}.example.com:${iblock_name}"

vgchange -a y ${vgname}

echo "ls
cd /backstores
iblock/ create ${iblock_name} /dev/${vgname}/${iblock_name}
cd ../iscsi
create ${target_name}
cd /iscsi/${target_name}/tpg1/
luns/ create /backstores/iblock/${iblock_name}
portals/ create ${portals_ip}
set attribute authentication=0 demo_mode_write_protect=0 generate_node_acls=1 cache_dynamic_acls=1
cd /
saveconfig
exit
exit"|targetcli
echo ""

sleep 3
# For test
echo ${target_name}
echo ${portals_ip}
iscsiadm -m discovery -t st -p ${portals_ip}
iscsiadm -m node -T ${target_name} -p ${portals_ip}  -l
iscsiadm -m node -T ${target_name} -p ${portals_ip}  -u
