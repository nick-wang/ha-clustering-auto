#!/bin/bash
# Since my local server using own ssh key,
# change the keys of common file.

cp ~/.ssh/id_* ssh_keys

temp=$(cat ssh_keys/id_rsa.pub)
#sed -i "s#echo \"ssh.*#echo \"${temp}\" >> /root/.ssh/authorized_keys]]></source>#g" confs/autoyast/*.xml or using find |xargs

#sed -i "s#echo.*#echo \"${temp}\" >> /root/.ssh/authorized_keys]]></source>#g" confs/my_ha_inst.xml
#sed -i "s#echo.*#echo \"${temp}\" >> /root/.ssh/authorized_keys]]></source>#g" confs/openSUSE_leap.xml
#sed -i "s#echo.*#echo \"${temp}\" >> /root/.ssh/authorized_keys]]></source>#g" confs/openSUSE42.1_leap_bliu.xml
sed -i "s#echo \"ssh.*#echo \"${temp}\" >> /root/.ssh/authorized_keys]]></source>#g" confs/autoyast/autoinst-SLE15.xml
sed -i "s#echo \"ssh.*#echo \"${temp}\" >> /root/.ssh/authorized_keys]]></source>#g" confs/autoyast/autoinst-SLE15SP1.xml
sed -i "s#echo \"ssh.*#echo \"${temp}\" >> /root/.ssh/authorized_keys]]></source>#g" confs/autoyast/autoinst-SLE15SP1-sep-modules.xml
sed -i "s#echo.*#echo \"${temp}\" >> /root/.ssh/authorized_keys]]></source>#g" confs/autoyast/autoinst-SLE11-SLE12.xml
sed -i "s#echo.*#echo \"${temp}\" >> /root/.ssh/authorized_keys]]></source>#g" confs/autoyast/autoinst-SLE11-SLE12-GEO.xml
sed -i "s#echo.*#echo \"${temp}\" >> /root/.ssh/authorized_keys]]></source>#g" confs/autoyast/autoinst-openSUSE_leap.xml
sed -i "s#echo.*#echo \"${temp}\" >> /root/.ssh/authorized_keys]]></source>#g" confs/autoyast/autoinst-openSUSE_tumbleweed.xml
sed -i "s#echo.*#echo \"${temp}\" >> /root/.ssh/authorized_keys]]></source>#g" confs/autoyast/*.xml
