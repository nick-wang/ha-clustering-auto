#!/bin/bash

function usage()
{
  echo "$0 <WHICH_DISK_TO_PARTITION>"
  echo "<WHICH_DISK_TO_PARTITION> should a number like 1, 2, 3, etc..."
}

if [ $# -ne 1 ]
then
    usage
    exit -1
fi

function patch_the_code()
{
    # Patch0: fix-resync-never-connected.KNOWN.patch
    patches=(fix-resync-never-connected.KNOWN.patch)
    for c_dir in `ls`
    do
        if [ -d ${c_dir} ]
        then
            pushd ${c_dir} >/dev/null
            break
        fi
    done

    for patch in ${patches[@]}
    do
        debugRun patch -p1 <../${patch}
    done
    popd >/dev/null
}

#Import ENV conf
. cluster_conf
. scripts/functions
. scripts/drbd/drbd_functions

nextPhase "Launch $0"

# Should not change vgname unless upstream changed
vgname="scratch"
NUM=$1

sle_ver=($(getSLEVersion))
case ${sle_ver[0]} in
  42.1|42.2|*umbleweed*)
    # Need to install patch and rsyslog in leap42.2
    ins_packages=(exxe fio logscan drbd-test patch rsyslog python3)
    ins_src_packages=(drbd-test)

    # Install all needed packages
    # rsyslog conflicting with systemd-syslog
    infoRun zypper --non-interactive install --force-resolution ${ins_packages[*]}
    ;;
  11|12|15)
    if [ "$sle_ver[0]" = "15" ]
    then
        ins_packages=(exxe fio logscan drbd-test python3 python3-PyYAML)
    else
        ins_packages=(exxe fio logscan drbd-test python-PyYAML)
    fi

    ins_src_packages=(drbd-test)

    # Install all needed packages
    infoRun zypper --non-interactive install ${ins_packages[*]}
    ;;
  *)
    echo "Not support. SLE${sle_ver[0]} SP${sle_ver[1]}"
esac

# Create a work directory
debugRun mkdir /drbdtest

# LVM configuration
# Convert to disk name via number
temp=$(nconvert ${NUM})
disk="/dev/vd${temp}"

debugRun pvcreate ${disk}
debugRun vgcreate ${vgname} ${disk}

# Install src packages for jobs define
infoRun zypper --non-interactive install -t srcpackage ${ins_src_packages[*]}

# Change to working dir
debugRun cp /usr/src/packages/SOURCES/* /drbdtest
pushd /drbdtest >/dev/null
debugRun tar xvf drbd-test-*.tar.bz2
patch_the_code
popd >/dev/null
