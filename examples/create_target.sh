#!/bin/bash

function usage()
{
  echo "create_target.sh -i <ISCSI_BLOCK_NAME> -v <VOLUME_GROUP> -n <NET_CARD> -c (-s <SIZE>)"
  echo "  args: [-i, -v, -n, -s, -c] [--iblock=, --vg=, --net=, --size=, --create=]"
  echo "    -c: need to create lv before creating target."
  echo "    -s: lvm disk size."
  echo "  example: create_target.sh -i nick-block1 -v ha-group [-n eth0 -c -s 500M]"
}

opt_name=""
opt_vg=""
opt_net=""
opt_create_lvm="no"

GETOPT_ARGS=`getopt -o i:v:n:s:c -al iblock:,vg:,net:,size:,create -- "$@"`
eval set -- "$GETOPT_ARGS"

function create_lvm()
{
    size=${3:-"128M"}
    echo "Creating lvm...  lvcreate $1 -n $2 -L $size"
    lvcreate $1 -n $2 -L $size
}

while [ -n "$1" ]
do
    case "$1" in
        -i|--iblock) opt_name=$2; shift 2;;
        -v|--vg) opt_vg=$2; shift 2;;
        -n|--net) opt_net=$2; shift 2;;
        -s|--size) opt_size=$2; shift 2;;
        -c|--create) opt_create_lvm="yes"; shift 1;;
        --) break ;;
    esac
done

if [ -z $opt_name ] || [ -z $opt_vg ]
then 
    usage
    exit -1
fi

if [ "yes" == $opt_create_lvm ]
then
    create_lvm $opt_vg $opt_name $opt_size
fi

iblock_name=${opt_name}
vgname=${opt_vg}
net=${opt_net:="eth0"}

year=`date +%y`
month=`date +%m`
target_name="iqn.20${year}-${month}.example.com:${iblock_name}"
portals_ip=`ip a | grep -A 2 " ${net}:" |sed -n "s/.*inet \(.*\)\/.*/\1/p"`

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
yes
exit"|targetcli
echo ""

sleep 2
# For test
echo ${target_name}
echo ${portals_ip}
iscsiadm -m discovery -t st -p ${portals_ip}
iscsiadm -m node -T ${target_name} -p ${portals_ip}  -l
iscsiadm -m node -T ${target_name} -p ${portals_ip}  -u
