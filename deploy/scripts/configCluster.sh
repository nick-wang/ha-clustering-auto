#!/bin/bash

#Import ENV conf
. cluster_conf
. scripts/functions

hosts_content=""
csync2_content=""
NUM_SHARED_TARGETS=`grep SHARED_TARGET_LUN cluster_conf | wc -l`
TARGET_LUN=$SHARED_TARGET_LUN1
TARGET_IP=$SHARED_TARGET_IP1
cd template

#Add extra repos
R_NUM=0
if [ -n $EXTRA_REPOS ]
then
  for repo in ${EXTRA_REPOS[@]}
  do
    # -G is Disable GPG check
    # or set repo_gpgcheck=no in /etc/zypp/zypp.conf
    zypper ar -f -G ${repo} CUSTOM_${R_NUM}
    R_NUM=$((R_NUM+1))
  done
fi

#Modify template according to cluster configuration
temp=$NODES
while [ "$temp" -ge 1 ]
do
    temp_ip=$(eval echo \$IP_NODE${temp})
    temp_hostname=$(eval echo \$HOSTNAME_NODE${temp})

    #Configure hosts_template
    sed -i "/^127.0.0.1/a$temp_ip   $temp_hostname" hosts_template

    #Configure csync2 (optional)
    sed -i "/^{/a\	host $temp_hostname;" csync2.cfg_template

    #Configure corosync.conf
    #Only support one ring
    sed -i "/^nodelist/a\    node {\n\
	ring0_addr:	$temp_ip\n\
	}\n" corosync.conf_template
    sed -i "/^\tinterface/a\ \t\tmember {\n\t\tmemberaddr: $temp_ip\n\t\t}\n" corosync.conf_template_1.4.7
    temp=$((temp-1))
done

#Modify bindnetaddr/port/quorum of corosync.conf
#Only support ring0 so far
bindnetaddr=$IP_NODE1
#Uncomment if using subnet as bindaddr
#ip=$IP_NODE1
#mask=255.255.255.0
#bindnetaddr=$(awk -vip="$ip" -vmask="$mask" 'BEGIN{
#>   sub("addr:","",ip);
#>   sub("Mask:","",mask);
#>   split(ip,a,".");
#>   split(mask,b,".");
#>   for(i=1;i<=4;i++)
#>     s[i]=and(a[i],b[i]);
#>   subnet=s[1]"."s[2]"."s[3]"."s[4];
#>   print subnet;
#> }')
sed -i "s/bindnetaddr:.*/bindnetaddr:	${bindnetaddr}/" corosync.conf_template
sed -i "s/mcastport:.*/mcastport:	${PORT:-5405}/" corosync.conf_template
sed -i "s/expected_votes:.*/expected_votes:	${NODES}/" corosync.conf_template
sed -i "s/bindnetaddr:.*/bindnetaddr:	${bindnetaddr}/" corosync.conf_template_1.4.7
sed -i "s/mcastport:.*/mcastport:	${PORT:-5405}/" corosync.conf_template_1.4.7
if [ 2 -eq "$NODES" ]
then
    sed -i "s/two_node:.*/two_node:	1/" corosync.conf_template
else
    sed -i "s/two_node:.*/two_node:	0/" corosync.conf_template
fi

#Install configuration files.
# /etc/hosts
# /etc/csync2/csync2.cfg
# /etc/csync2/key_hagroup
# /etc/corosync/corosync.conf
cp -rf hosts_template /etc/hosts
cp -rf csync2.cfg_template /etc/csync2/csync2.cfg
cp -rf key_hagroup_template /etc/csync2/key_hagroup
cp -rf corosync.conf_template /etc/corosync/corosync.conf

#Disable hostkey checking of ssh
grep "^ *StrictHostKeyChecking" /etc/ssh/ssh_config >/dev/null
if [ $? -ne 0 ]
then
    sed -i "/^# *StrictHostKeyChecking ask/a\StrictHostKeyChecking no" \
        /etc/ssh/ssh_config
fi

#update ha packages
zypper up -y -l -t pattern ha_sles

#login iscsi target for sbd
#and create sbd
iscsiadm -m discovery -t st -p $TARGET_IP >/dev/null
iscsiadm -m node -T $TARGET_LUN -p $TARGET_IP -l
sleep 15

#judge the stonith type
if [ $STONITH == "libvirt" ];
then
    zypper in -y libvirt
else
    sbd -d "/dev/disk/by-path/ip-$TARGET_IP:3260-iscsi-${TARGET_LUN}-lun-0" create
    modprobe softdog
    echo "SBD_DEVICE='/dev/disk/by-path/ip-$TARGET_IP:3260-iscsi-${TARGET_LUN}-lun-0'" > /etc/sysconfig/sbd
    echo "SBD_OPTS='-W'" >> /etc/sysconfig/sbd
    echo "modprobe softdog" >> /etc/init.d/boot.local
fi

#Open ports if firewall enabled
#Default disable after installation

#Enable service
sle_ver=($(echo $(getSLEVersion)))
case ${sle_ver[0]} in
  12|42.1|42.2)
    systemctl enable iscsid.socket
    systemctl enable iscsiuio.socket
    systemctl enable iscsi.service
    systemctl enable csync2.socket
    systemctl enable pacemaker

    #Start service
    systemctl start csync2.socket
    systemctl start pacemaker
    ;;
  11)
    chkconfig open-iscsi on
    chkconfig csync2 on
    chkconfig openais on
    cp -rf corosync.conf_template_1.4.7 /etc/corosync/corosync.conf
    cp -rf authkey /etc/corosync/

    service openais start
    ;;
  *)
    echo "Not support. SLE${sle_ver[0]} SP${sle_ver[1]}"
esac

#Enable automatic login to iscsi server
iscsiadm -m node -I default -T $TARGET_LUN -p $TARGET_IP \
         --op=update --name=node.startup --value=automatic
if [ $? -ne 0 ]; then
	echo "failed to login $TARGET_LUN on $TARGET_IP"
	exit -1
fi
#login other target for shared storage
if [ $NUM_SHARED_TARGETS -gt 1 ];then
    for i in `seq 2 $NUM_SHARED_TARGETS`; do
        name=`echo "SHARED_TARGET_IP$i"`
        tgt_ip=`getEnv $name ../cluster_conf`
        name=`echo "SHARED_TARGET_LUN$i"`
        tgt_lun=`getEnv $name ../cluster_conf`

        iscsiadm -m node -T $tgt_lun -p $tgt_ip -l
        #Enable automatic login to iscsi server
        iscsiadm -m node -I default -T $tgt_lun -p $tgt_ip \
             --op=update --name=node.startup --value=automatic
    done
fi
#config stonith resource and restart pacemaker
isMaster "$HOSTNAME_NODE1"
if [ $? -eq 0 ]
then
    if [ $STONITH == "sbd" ];
    then
        crm configure primitive stonith_sbd stonith:external/sbd
    else
        crm configure primitive libvirt_stonith stonith:external/libvirt \
                  params hostlist="$NODE_LIST" \
                  hypervisor_uri="qemu+tcp://$IPADDR/system" \
                  op monitor interval="60"
    fi
fi
sleep 2
case ${sle_ver} in
  12|42.1|42.2)
    if [ $STONITH == "sbd" ];
    then
        systemctl enable sbd
    fi
    systemctl restart pacemaker
    systemctl enable hawk
    systemctl start hawk
    ;;
  11)
    if [ $STONITH == "sbd" ];
    then
        chkconfig sbd on
    fi
    service openais restart
    chkconfig hawk on
    rchawk start
    ;;
  *)
    echo "Not support. SLE${sle_ver[0]} SP${sle_ver[1]}"
esac

#update password for hacluster
passwd hacluster > /dev/null 2>&1 <<EOF
linux
linux
EOF
