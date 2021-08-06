#!/bin/bash

#Import ENV conf
. cluster_conf
. scripts/functions

hosts_content=""
csync2_content=""
TARGET_LUN=$SHARED_TARGET_LUN0
TARGET_IP=$SHARED_TARGET_IP0
i=0
for ip in `cat cluster_conf |grep IP_NODE |cut -d "=" -f 2`
do
	let i+=1
	ip a|grep inet|grep "${ip}/" > /dev/null
	if [ $? -eq 0 ]; then
		echo "Change hostname on IP:${ip}."
		host_name=`cat cluster_conf | grep "HOSTNAME_NODE$i"|cut -d "=" -f 2`
		# For systemd, may use "hostnamectl set-hostname $host_name"
		hostname $host_name
		echo "$host_name" > /etc/HOSTNAME
		echo "$host_name" > /etc/hostname

		# In Tumbleweed 20210524, no /etc/iscsi/initiatorname.iscsi in open-iscsi by default
		if [ -e /etc/iscsi/initiatorname.iscsi ]; then
			echo "Replace the initiatorname in /etc/iscsi/initiatorname.iscsi:"
			sed -i "/^InitiatorName/s/.*/&-${host_name}/" /etc/iscsi/initiatorname.iscsi
			cat /etc/iscsi/initiatorname.iscsi |grep "^InitiatorName"
		fi
	fi
done

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

# save log messages after reboot
sed -i '/#Storage/a Storage=persistent' /etc/systemd/journald.conf

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
if [ -e /etc/ssh/ssh_config ]
then
    grep "^ *StrictHostKeyChecking" /etc/ssh/ssh_config >/dev/null
    if [ $? -ne 0 ]
    then
        sed -i "/^# *StrictHostKeyChecking ask/a\StrictHostKeyChecking no" \
            /etc/ssh/ssh_config
    fi
else
	echo "StrictHostKeyChecking no" >> /etc/ssh/ssh_config
fi

#update ha packages
zypper in -y -l open-iscsi iscsiuio ntp chrony
zypper up -y -l -t pattern ha_sles

#Login and enable automatic login of iscsi target
#TODO: remove if seperate SBD from iscsi target list.
if [ $STONITH == "libvirt" ];
then
    START_NUM=1
else
    START_NUM=0
fi

for i in `seq $START_NUM $NUM_SHARED_TARGETS`; do
    name=`echo "SHARED_TARGET_IP$i"`
    tgt_ip=`getEnv $name ../cluster_conf`
    name=`echo "SHARED_TARGET_LUN$i"`
    tgt_lun=`getEnv $name ../cluster_conf`

    #In Tumbleweed 20210524, link /bin/systemctl is removed. Then added back in 20210730...
    if [ -e /usr/bin/systemctl ]; then
        sed -i "$ a iscsid.startup = /usr/bin/systemctl start iscsid.socket iscsiuio.socket" /etc/iscsi/iscsid.conf
    elif [ -e /bin/systemctl ]; then
        sed -i "$ a iscsid.startup = /bin/systemctl start iscsid.socket iscsiuio.socket" /etc/iscsi/iscsid.conf
    fi

	#For SBD, the login may fail. But it won't effect the result
    iscsiadm -m discovery -t st -p $tgt_ip > /dev/null
    iscsiadm -m node -T $tgt_lun -p $tgt_ip -l

    #Enable automatic login to iscsi server
    iscsiadm -m node -I default -T $tgt_lun -p $tgt_ip \
         --op=update --name=node.startup --value=automatic
done
#sync the time
sle_ver=($(getSLEVersion))
case ${sle_ver[0]} in
  # ${sle_ver[0]} maybe openSUSETumbleweed/tumbleweed*
  15|*umbleweed*)
    systemctl enable chronyd.service

    # Add NTP server to /etc/chrony.conf
    sed -i '$aserver time.nist.gov iburst' /etc/chrony.conf

    systemctl restart chronyd.service

    # sync from NTP server
    chronyc -a makestep

    # Check NTP sync status
    chronyc sources -v
    ;;
  *)
    ntpdate time.nist.gov
esac
#judge the stonith type
#create sbd if using sbd as stonith
if [ $STONITH == "libvirt" ];
then
    zypper in -y libvirt
	# Temporily fix for bsc#1186576, need extra pacemaker>=2.1.0 repo
	# https://download.opensuse.org/repositories/home:/yan_gao:/branches:/network:/ha-clustering:/Factory:/Test/openSUSE_Tumbleweed/
	# Only available for libvirt, since the pacemaker conflict to sbd
	zypper up --allow-vendor-change --force-resolution -y pacemaker
else
    sleep 15
    # To use sbd, should configure at least one iscsi target - $SHARED_TARGET_LUN0
    sbd -d "/dev/disk/by-path/ip-${TARGET_IP}:3260-iscsi-${TARGET_LUN}-lun-0" create
    modprobe softdog
    echo "SBD_DEVICE='/dev/disk/by-path/ip-${TARGET_IP}:3260-iscsi-${TARGET_LUN}-lun-0'" > /etc/sysconfig/sbd
    echo "SBD_OPTS='-W'" >> /etc/sysconfig/sbd

    # Using systemd way to handle startup commands
    case ${sle_ver[0]} in
      15|12|42.1|42.2|*umbleweed*)
        echo "[Unit]
After=network.service

[Service]
ExecStart=/usr/local/bin/start-softdog.sh

[Install]
WantedBy=default.target
" > /etc/systemd/system/ci-softdog.service

        echo "#!/bin/bash
modprobe softdog
" > /usr/local/bin/start-softdog.sh

        chmod 744 /usr/local/bin/start-softdog.sh

        systemctl enable ci-softdog.service
        systemctl restart ci-softdog.service

        ;;
      *)
        echo "modprobe softdog" >> /etc/init.d/boot.local
    esac

fi

#Open ports if firewall enabled
#Default disable after installation

#Enable service
infoLog "Enable services and start pacemaker."
case ${sle_ver[0]} in
  15|12|42.1|42.2|*umbleweed*)
    zypper in -y systemd-rpm-macros
    systemctl enable iscsid.socket
    systemctl enable iscsiuio.socket
    systemctl enable iscsi.service
    systemctl enable csync2.socket
    systemctl enable pacemaker
    systemctl enable hawk
    if [ $STONITH == "sbd" ];
    then
        systemctl enable sbd
    fi

    sleep 2

    #Start service
    systemctl start csync2.socket
    systemctl start pacemaker
    systemctl start hawk
    ;;
  11)
    chkconfig open-iscsi on
    chkconfig csync2 on
    chkconfig openais on
    chkconfig hawk on
    cp -rf corosync.conf_template_1.4.7 /etc/corosync/corosync.conf
    cp -rf authkey /etc/corosync/

    if [ $STONITH == "sbd" ];
    then
        chkconfig sbd on
    fi

    sleep 2

    #Start service
    service openais start
    rchawk start
    ;;
  *)
    echo "!!!ERROR!!! Not support. SLE${sle_ver[0]} SP${sle_ver[1]}"
esac

#update password for hacluster
passwd hacluster > /dev/null 2>&1 <<EOF
linux
linux
EOF
