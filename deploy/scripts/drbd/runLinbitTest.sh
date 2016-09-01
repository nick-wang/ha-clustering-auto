#!/bin/bash
function usage()
{
  echo "$0 <CLUSTER_CONF_IN_HOST> <WORKING_DIR_IN_GUEST>"
}

if [ $# -ne 2 ]
then
  usage
  exit -1
fi

#Import ENV conf
. functions

CLUSTER_CONF=$1
CLUSTER_DIR=$2

cpToNodes ${CLUSTER_CONF} "drbd/drbd_functions" "${CLUSTER_DIR}/scripts/drbd/"
cpToNodes ${CLUSTER_CONF} "drbd/libs/setupLinbitTestEnv.sh drbd/libs/LinbitTest.py drbd/libs/cleanLinbitTest.py" "${CLUSTER_DIR}/scripts/drbd/libs/"

nextPhase "Launch setupLinbitTestEnv.sh (${CLUSTER_CONF})"
runOnAllNodes ${CLUSTER_CONF} "cd ${CLUSTER_DIR}; ${CLUSTER_DIR}/scripts/drbd/libs/setupLinbitTestEnv.sh 1"

nextPhase "Launch LinbitTest.py on HOSTNAME_NODE1 (${CLUSTER_CONF})"
runOnMasterNodes ${CLUSTER_CONF} "HOSTNAME_NODE1" "cd ${CLUSTER_DIR}; ${CLUSTER_DIR}/scripts/drbd/libs/LinbitTest.py"

nextPhase "Log collection (${CLUSTER_CONF})"
