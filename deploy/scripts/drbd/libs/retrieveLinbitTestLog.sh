#!/bin/bash

function usage()
{
  echo "$0 <CLUSTER_CONF_IN_HOST> <LOG_DIR_IN_HOST> <LOGS_LIST>"
}

if [ $# -ne 3 ]
then
  usage
  exit -1
fi

#Import ENV conf
. functions

CLUSTER_CONF=$1
LOG_DIR=$2
LOGS_LIST=$3

retrieveLogsFromNode ${CLUSTER_CONF} "HOSTNAME_NODE1" ${LOG_DIR} ${LOGS_LIST}
