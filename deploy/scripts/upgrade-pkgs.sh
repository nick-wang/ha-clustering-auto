#!/bin/bash
function usage()
{
  echo "$0 <CLUSTER_CONF_IN_HOST> <LOG_DIR> (<PACKAGES>)"
}

if [ $# -ne 2 ] && [ $# -ne 3 ]
then
  usage
  exit -1
fi

#Import ENV conf
. functions

CLUSTER_CONF=$1
LOG_DIR=$2

if [ $# -eq 3 ]
then
    pkgs=($3)
else
    pkgs=(kernel-default drbd drbd-utils drbd-kmp-default pacemaker corosync lvm2)
fi

runOnAllNodes ${CLUSTER_CONF} "rpm -qa|sort>${LOG_DIR}/rpm-before-update-pkgs"

nextPhase "Upgrading..."
# Can not use ${pkgs[@]}, could use ${pkgs[*]}
# Allow verdor change for upgrade
runOnAllNodes ${CLUSTER_CONF} "sed -i \"s/# solver.allowVendorChange = false/solver.allowVendorChange = true\"/ /etc/zypp/zypp.conf; cat /etc/zypp/zypp.conf |grep allowVendorChange"

# Remove the old version and reinstall the new version
# Sometimes need to update kernel-default as well, so add kernel repo
runOnAllNodes ${CLUSTER_CONF} "rm -rf ${LOG_DIR}/done; zypper -q -n rm ${pkgs[*]}; zypper -q -n in --replacefiles ${pkgs[*]}; sleep 1; touch ${LOG_DIR}/update-pkgs-done; reboot"

checkAllFinish ${CLUSTER_CONF} "${LOG_DIR}/update-pkgs-done"

nextPhase "Upgrade finished and system rebooted."
runOnAllNodes ${CLUSTER_CONF} "rpm -qa|sort>${LOG_DIR}/rpm-after-update-pkgs"
