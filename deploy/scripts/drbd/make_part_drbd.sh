#!/bin/bash

function usage()
{
  echo "make_part_drbd.sh <HOW_MANY_DISKS_TO_PATITION>"
  echo "<HOW_MANY_DISKS_TO_PARTITION> should equal <HOW_MANY_DISKS_TO_ADD> of addVirioDisk.sh"
}

if [ $# -ne 1 ]
then
    usage
    exit -1
fi

# How many disks need to partition
NUM=$1

function nconvert()
{
echo -n $1 | tr "123456789" "bcdefghij"
}

# Convert to disk name via numbers
i=1
while [ $i -le $NUM ]
do
  temp=$(nconvert ${i})
  disks[${i}]=/dev/vd${temp}
  i=$((i+1))
done
echo ${disks[@]}

#Partition
for disk in ${disks[@]}
do
# Plan to create 3 resources.
# multi-res:
#   drbd0 - /dev/vdb1,
#     meta-disk: /dev/vdb6
#   drbd1 - /dev/vdb2,
#     meta-disk: /dev/vdb7
# first-res:
#   drbd2 - /dev/vdb3,
#     meta-disk: /dev/vdb8
# second-res:
#   drbd3 - /dev/vdb5,
#     meta-disk: /dev/vdb9
#
# Disk /dev/vdb: 3 GiB, 3221225472 bytes, 6291456 sectors
# Units: sectors of 1 * 512 = 512 bytes
# Sector size (logical/physical): 512 bytes / 512 bytes
# I/O size (minimum/optimal): 512 bytes / 512 bytes
# Disklabel type: dos
# Disk identifier: 0x28da74e2
#
# Device     Boot   Start     End Sectors  Size Id Type
# /dev/vdb1          2048 1026047 1024000  500M 83 Linux
# /dev/vdb2       1026048 2254847 1228800  600M 83 Linux
# /dev/vdb3       2254848 3893247 1638400  800M 83 Linux
# /dev/vdb4       3893248 6291455 2398208  1.1G  5 Extended
# /dev/vdb5       3895296 5992447 2097152    1G 83 Linux
# /dev/vdb6       5994496 6055935   61440   30M 83 Linux
# /dev/vdb7       6057984 6119423   61440   30M 83 Linux
# /dev/vdb8       6121472 6182911   61440   30M 83 Linux
# /dev/vdb9       6184960 6291455  106496   52M 83 Linux
echo "n
p
1

+500M
n
p
2

+600M
n
p
3

+800M
n
e


n

+1G
n

+30M
n

+30M
n

+30M
n


w
"|fdisk ${disk}
done

partprobe