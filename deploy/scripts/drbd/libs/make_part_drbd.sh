#!/bin/bash

function usage()
{
  echo "make_part_drbd.sh <WHICH_DISK_TO_PARTITION>"
  echo "<WHICH_DISK_TO_PARTITION> should a number like 1, 2, 3, etc..."
  echo "Should call this script multiple times for multiple disks."
}

if [ $# -ne 1 ]
then
    usage
    exit -1
fi

#Import ENV conf
. scripts/functions
. scripts/drbd/drbd_functions

nextPhase "Launch $0"

# which disk need to partition
NUM=$1

# Convert to disk name via numbers
temp=$(nconvert ${NUM})
disk=/dev/vd${temp}

#Partition
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

+200M
n
p
2

+300M
n
p
3

+400M
n
e


n

+10M
n

+20M
n

+20M
n

+20M
n


w
"|fdisk ${disk}

nextPhase "Finished partitioning ${disk}" | tee -a ${DRBD_LOGFILE}
infoRun fdisk -l ${disk} | tee -a ${DRBD_LOGFILE}

partprobe
