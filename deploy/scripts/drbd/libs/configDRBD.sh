#!/bin/bash

# Environment to control how to configure
# Need to configure manually
# ================================================================
# For example:
# /dev/drbd(0) --> disk: /dev/vdb(1) --> meta-disk: /dev/vdb(6)
#     MINORS[0]="1 6"
# /dev/drbd(0) --> disk: /dev/vdb(1) --> meta-disk: internal
#     MINORS[0]="1"
NUM_MULTI=1
MINORS[0]="1 6"
MINORS[1]="2 7"

NUM_SINGLE=3
MINORS[2]="3 8"
MINORS[3]="5"
MINORS[4]="9"
# ================================================================

function usage()
{
  echo "configDRBD.sh <DISK> (<CONFIG_PREFIX>)"
  echo "  <DISK>: eg. /dev/vdb"
  echo "  <CONFIG_PREFIX>: eg. bj-"
  exit
}

if [ $# -gt 2 ] || [ $# -eq 0 ]
then
    usage
    exit -1
fi

#Import ENV conf
. cluster_conf
. scripts/functions
. scripts/drbd/drbd_functions

nextPhase "Launch $0"

# Get disk like /dev/vdb
DISK=$1
# PRE_FIX="" when no $2 para
if [ -n $2 ]
then
  PRE_FIX=${2}-
fi

cd template/drbd
start_port=7788
cur_minor=0

# Modify drbd template according to cluster configuration
# Configure a multi-volume resource
# Same paras of drbd8/9
i=0
while [ $i -lt $NUM_MULTI ]
do
  # Need to set two volumes when multiple configuration
  m=0
  while [ $m -lt 2 ]
  do
    minor[${m}]=${cur_minor}

    if [ ${#MINORS[$cur_minor]} -eq 1 ]
    then
      disk[${m}]=${DISK}${MINORS[$cur_minor]}
      metadisk[${m}]=internal
    elif [ ${#MINORS[$cur_minor]} -eq 3 ]
    then
      set -- ${MINORS[$cur_minor]}
      disk[${m}]=${DISK}${1}
      metadisk[${m}]=${DISK}${2}
    else
      echo "Error input of disk/metadisk: ${MINORS[$cur_minor]}"
      exit -1
    fi

    cur_minor=$((minor+1))
    m=$((m+1))
  done
  #echo ${minor[@]}
  #echo ${disk[@]}
  #echo ${metadisk[@]}

  case $(getDRBDVer) in
    9)
      echo "Configuring DRBD9 multi-res..."

      # Configuring "on" and connection-mesh sections for multiple nodes
      # ON section:
      # on="   on <name> {\n\
      #     address   <IP_ADDR>;\n\
      #     node-id   <NODEID>;\n\
      #  }"
      nodeid=1
      on_section=""
      all_nodes=()
      while [ $nodeid -le $NODES ]
      do
        nodename=$(eval echo \$HOSTNAME_NODE${nodeid})
        nodeaddr=$(eval echo \$IP_NODE${nodeid})
        on_section=${on_section}"\n   on ${nodename} {\n\
      address   ${nodeaddr}:${start_port};\n\
      node-id   ${nodeid};\n\
   }"
        all_nodes[${nodeid}]=${nodename}
        nodeid=$((nodeid+1))
      done
      #echo "$on_section"
      #echo "${all_nodes[*]}"

      sed "s#<RESNAME>#${PRE_FIX}multi-${i}#g;
           s#<DEVICE_VO0>#/dev/drbd${minor[0]}#g;
           s#<DISK_VO0>#${disk[0]}#g;
           s#<METADISK_VO0>#${metadisk[0]}#g;
           s#<DEVICE_VO1>#/dev/drbd${minor[1]}#g;
           s#<DISK_VO1>#${disk[1]}#g;
           s#<METADISK_VO1>#${metadisk[1]}#g;
           s#<ON>#${on_section}#g;
           s#<ALL_NODES>#${all_nodes[*]}#g;
      " drbd_multi_v9.res_template > ${PRE_FIX}multi-${i}.res

      ;;
    84)
      echo "Configuring DRBD8 multi-res..."
      sed "s#<RESNAME>#${PRE_FIX}multi-${i}#g;
           s#<DEVICE_VO0>#/dev/drbd${minor[0]}#g;
           s#<DISK_VO0>#${disk[0]}#g;
           s#<METADISK_VO0>#${metadisk[0]}#g;
           s#<DEVICE_VO1>#/dev/drbd${minor[1]}#g;
           s#<DISK_VO1>#${disk[1]}#g;
           s#<METADISK_VO1>#${metadisk[1]}#g;
           s#<NODE1>#${HOSTNAME_NODE1}#g;
           s#<NODE1_IP_PORT>#${IP_NODE1}:${start_port}#g;
           s#<NODE2>#${HOSTNAME_NODE2}#g;
           s#<NODE2_IP_PORT>#${IP_NODE2}:${start_port}#g;
      " drbd_multi_v8.res_template > ${PRE_FIX}multi-${i}.res
      ;;

    *)
      echo "Error! Wrong DRBD version."
  esac
  echo "include \"/etc/drbd.d/${PRE_FIX}multi-${i}.res\";" >> drbd_drbd.conf_template

  i=$((i+1))
  cur_minor=$((cur_minor+1))
  start_port=$((start_port+4))
done

# Modify drbd template according to cluster configuration
# Configure a single-volume resource
# Same paras of drbd8/9
i=0
while [ $i -lt $NUM_SINGLE ]
do
  minor=${cur_minor}
  if [ ${#MINORS[$cur_minor]} -eq 1 ]
  then
    disk=${DISK}${MINORS[$cur_minor]}
    metadisk=internal
  elif [ ${#MINORS[$cur_minor]} -eq 3 ]
  then
    set -- ${MINORS[$cur_minor]}
    disk=${DISK}${1}
    metadisk=${DISK}${2}
  else
    echo "Error input of disk/metadisk: ${MINORS[$cur_minor]}"
    exit -1
  fi
  #echo ${minor}
  #echo ${disk}
  #echo ${metadisk}

  case $(getDRBDVer) in
    9)
      echo "Configuring DRBD9 single-res..."
      # Configuring "on" and connection-mesh sections for multiple nodes
      # ON section:
      # on="   on <name> {\n\
      #     address   <IP_ADDR>;\n\
      #     node-id   <NODEID>;\n\
      #  }"
      nodeid=1
      on_section=""
      all_nodes=()
      while [ $nodeid -le $NODES ]
      do
        nodename=$(eval echo \$HOSTNAME_NODE${nodeid})
        nodeaddr=$(eval echo \$IP_NODE${nodeid})
        on_section=${on_section}"\n   on ${nodename} {\n\
      address   ${nodeaddr}:${start_port};\n\
      device    /dev/drbd${minor};\n\
      disk      ${disk};\n\
      meta-disk ${metadisk};\n\
      node-id   ${nodeid};\n\
   }"
        all_nodes[${nodeid}]=${nodename}
        nodeid=$((nodeid+1))
      done

      sed "s#<RESNAME>#${PRE_FIX}single-${i}#g;
           s#<ON>#${on_section}#g;
           s#<ALL_NODES>#${all_nodes[*]}#g;
      " drbd_single_v9.res_template > ${PRE_FIX}single-${i}.res

      ;;
    84)
      echo "Configuring DRBD8 single-res..."

      sed "s#<RESNAME>#${PRE_FIX}single-${i}#g;
           s#<DEVICE>#/dev/drbd${minor}#g;
           s#<DISK>#${disk}#g;
           s#<METADISK>#${metadisk}#g;
           s#<NODE1>#${HOSTNAME_NODE1}#g;
           s#<NODE1_IP_PORT>#${IP_NODE1}:${start_port}#g;
           s#<NODE2>#${HOSTNAME_NODE2}#g;
           s#<NODE2_IP_PORT>#${IP_NODE2}:${start_port}#g;
      " drbd_single_v8.res_template > ${PRE_FIX}single-${i}.res
      ;;

    *)
      echo "Error! Wrong DRBD version."
  esac
  echo "include \"/etc/drbd.d/${PRE_FIX}single-${i}.res\";" >> drbd_drbd.conf_template

  i=$((i+1))
  cur_minor=$((cur_minor+1))
  start_port=$((start_port+4))
done

# Copy templates to the right location
# Running multiple times configDRBD.sh can overlap the old drbd.conf successfully
cp *.res /etc/drbd.d/
cp drbd_global_common.conf_template /etc/drbd.d/global_common.conf
cp drbd_drbd.conf_template /etc/drbd.conf

# Add quorum off; when two nodes DRBD cluster
if [ "$NODES" -eq 2 ]
then
    sed -i "/common/a\  options { \n     quorum off;\n  }" /etc/drbd.d/global_common.conf
fi

#Create meta-data on all nodes
drbdadm create-md all
sleep 5

# Stop the susefirewall2
# Since SLE15, change to firewalld which is disable by default
rcSuSEfirewall2 stop 2>/dev/null

# In tumbleweed, firewalld is enable by default
which firewalld && (systemctl disable firewalld ; \
systemctl stop firewalld ; systemctl status firewalld)

# Start the drbd service for the first sync
# Starting res one by one instead of using `rcdrbd start`
#   to avoid failure of alloc_ordered_workqueue()
for res in `drbdadm sh-resources`
do
  drbdadm up $res
  sleep 3
done

#Sometimes it need time to wait peer node to showup
sleep 15

echo "DRBD resources should connected with inconsistent data, $HOSTNAME"
showDRBDStatus "all"

# Run on each node for each resource
for res in `drbdadm sh-resources`
do
  reconnectStandAloneRes $res
done
