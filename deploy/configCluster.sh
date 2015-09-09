#!/bin/bash

#Import ENV conf
. cluster_conf

hosts_content=""
csync2_content=""

#Modify templete according to cluster configuration
temp=$NODES
while [ "$temp" -ge 1 ]
do
    temp_ip=$(eval echo \$IP_NODE${temp})
    temp_hostname=$(eval echo \$HOSTNAME_NODE${temp})

    #Configure hosts_templete
    sed -i "/^127.0.0.1/a$temp_ip   $temp_hostname" hosts_templete

    #Configure csync2 (optional)
    sed -i "/^{/a\	host $temp_hostname;" csync2.cfg_templete

    #Configure corosync.conf
    #Only support one ring
    sed -i "/^nodelist/a\    node {\n\
	ring0_addr:	$temp_ip\n\
	}\n" corosync.conf_templete

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
sed -i "s/bindnetaddr:.*/bindnetaddr:	${bindnetaddr}/" corosync.conf_templete
sed -i "s/mcastport:.*/mcastport:	${PORT:-5405}/" corosync.conf_templete
sed -i "s/expected_votes:.*/expected_votes:	${NODES}/" corosync.conf_templete
if [ 2 -eq "$NODES" ]
then
    sed -i "s/two_node:.*/two_node:	1/" corosync.conf_templete
else
    sed -i "s/two_node:.*/two_node:	0/" corosync.conf_templete
fi

#Install configuration files.
# /etc/hosts
# /etc/csync2/csync2.cfg
# /etc/csync2/key_hagroup
# /etc/corosync/corosync.conf
cp -rf hosts_templete /etc/hosts
cp -rf csync2.cfg_templete /etc/csync2/csync2.cfg
cp -rf key_hagroup_templete /etc/csync2/key_hagroup
cp -rf corosync.conf_templete /etc/corosync/corosync.conf

#Disable hostkey checking of ssh
grep "^ *StrictHostKeyChecking" /etc/ssh/ssh_config >/dev/null
if [ $? -ne 0 ]
then
    sed -i "/^# *StrictHostKeyChecking ask/a\StrictHostKeyChecking no" \
        /etc/ssh/ssh_config
fi

#login iscsi target
#and create sbd
iscsiadm -m discovery -t st -p $TARGET_IP
iscsiadm -m node -T $TARGET_LUN -p $TARGET_IP -l
sleep 20
sbd -d "/dev/disk/by-path/ip-$TARGET_IP:3260-iscsi-$(TARGET_LUN)-lun-0" create
modprobe softdog
echo "SBD_DEVICE='/dev/disk/by-path/ip-$TARGET_IP:3260-iscsi-$(TARGET_LUN)-lun-0'" > /etc/sysconfig/sbd
echo "SBD_OPTS ='-W'" >> /etc/sysconfig/sbd
echo "modprobe softdog" >> /etc/init.d/boot.local


#Open ports if firewall enabled
#Default disable after installation

#Enable service
systemctl enable csync2.socket
systemctl enable pacemaker

#Start service
systemctl start csync2.socket
systemctl start pacemaker
