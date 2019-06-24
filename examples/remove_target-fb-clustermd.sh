#!/bin/bash

function usage()
{
  echo "remove_target -i <ISCSI_BLOCK_NAME> -v <VOLUME_GROUP>"
  echo "  args: [-i, -v] [--block=, --vg=]"
  echo "  example: remove_target -i nick-block1 -v ha-group"
}

block_name=""
vgname=""

GETOPT_ARGS=`getopt -o i:v: -al block:,vg: -- "$@"`
eval set -- "$GETOPT_ARGS"

function remove_lvm()
{
    echo "Remove lvm...  lvremove /dev/${1}/${2}"
    echo "y"| lvremove /dev/${1}/${2}
}

while [ -n "$1" ]
do
    case "$1" in
        -i|--block) block_name=$2; shift 2;;
        -v|--vg) vgname=$2; shift 2;;
        --) break ;;
    esac
done

if [ -z $block_name ] || [ -z $vgname ]
then 
    usage
    exit -1
fi

target_name=$(targetcli ls |sed -n "s/.*o- \(iqn.*:${block_name}\) .*/\1/p")

if [ -z ${target_name} ]
then
    echo "Can not find $block_name in target."
    exit -2
fi

echo "ls
cd /iscsi
delete ${target_name}
cd /backstores/block/
delete ${block_name}"0"
delete ${block_name}"1"
delete ${block_name}"2"
delete ${block_name}"3"
delete ${block_name}"4"
delete ${block_name}"5"
cd /
saveconfig
exit"|targetcli
echo ""

remove_lvm ${vgname} ${block_name}"0"
remove_lvm ${vgname} ${block_name}"1"
remove_lvm ${vgname} ${block_name}"2"
remove_lvm ${vgname} ${block_name}"3"
remove_lvm ${vgname} ${block_name}"4"
remove_lvm ${vgname} ${block_name}"5"
