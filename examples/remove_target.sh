#!/bin/bash

function usage()
{
  echo "remove_target -i <ISCSI_BLOCK_NAME> -v <VOLUME_GROUP>"
  echo "  args: [-i, -v] [--iblock=, --vg=]"
  echo "  example: remove_target -i nick-block1 -v ha-group"
}

iblock_name=""
vgname=""

GETOPT_ARGS=`getopt -o i:v: -al iblock:,vg: -- "$@"`
eval set -- "$GETOPT_ARGS"

function remove_lvm()
{
    size=${3:-"128M"}
    echo "Remove lvm...  lvremove /dev/${1}/${2}"
    echo "y"| lvremove /dev/${1}/${2}
}

while [ -n "$1" ]
do
    case "$1" in
        -i|--iblock) iblock_name=$2; shift 2;;
        -v|--vg) vgname=$2; shift 2;;
        --) break ;;
    esac
done

if [ -z $iblock_name ] || [ -z $vgname ]
then 
    usage
    exit -1
fi

target_name=$(targetcli ls |sed -n "s/.*o- \(iqn.*:${iblock_name}\) .*/\1/p")

if [ -z ${target_name} ]
then
    echo "Can not find $iblock_name in target"
    exit -2
fi

echo "ls
cd /iscsi
delete ${target_name}
cd /backstores/iblock/
delete ${iblock_name}
cd /
saveconfig
yes
exit"|targetcli
echo ""

remove_lvm ${vgname} ${iblock_name}
