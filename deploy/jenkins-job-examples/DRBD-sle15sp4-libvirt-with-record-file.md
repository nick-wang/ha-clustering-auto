# Prepare an environment for the run
##	Properties Content
```
LIB_DIR=/var/lib/jenkins-work/ha-share/deploy/scripts
WORK_DIR=/var/lib/jenkins-work/jobs/${JOB_NAME}/${BUILD_NUMBER}
CONFIG_CLUSTER_DIR=/var/lib/cluster-configuration
CLUSTER_FILE=${WORK_DIR}/cluster_conf
YAML_FILE=${WORK_DIR}/vm_list.yaml
BUILD_LOG_DIR=${WORKSPACE}/${BUILD_NUMBER}
```

##	Script Content
```
rm -rf ~/.ssh/known_hosts
```


# Restrict where this project can be run
```
HA-5
```


# Abort the build if it's stuck
## 	Time-out strategy
```
90
```

## Time-out variable
```
TIMEOUT
```

# Execute shell
```
# Create the dirs
mkdir -p ${WORK_DIR}

# To get the changed build URL
master_addr="10.67.160.200"
jenkins_container="jenkins-ci-host"
local_rec_file="/var/tmp/${JOB_NAME##*/}-${BUILD_NUMBER}"

# Check the remote file exists?
. ${LIB_DIR}/retrieveRecord.sh ${master_addr}:${jenkins_container} ${RECORD_FILE} ${local_rec_file}

source ${local_rec_file}
rm -rf ${local_rec_file}

# Create YAML_FILE
cat > ${YAML_FILE} << !EOF!
resources:
  sle_source: http://mirror.suse.asia/install/SLP/SLE-15-SP3-Full-Beta2/x86_64/DVD1/
  ha_source:  http://mirror.suse.asia/install/SLP/SLE-15-SP3-Full-Beta2/x86_64/DVD1/

nodes:
- name: SLE15-sp3-Beta2-drbd-node1
- name: SLE15-sp3-Beta2-drbd-node2

repos:
- repo: http://download.suse.de/ibs/SUSE:/SLE-15-SP3:/GA/standard/
- repo: http://download.suse.de/ibs/home:/wanghaisu:/branches:/SUSE:/SLE-15-SP3:/GA/standard/


devices:
  disk_dir: /mnt/vm/sles_nick
  nic: br0
  sharing_backing_file: yes


iscsi:
  target_ip: 10.67.160.200
  shared_target_luns:
  - shared_target_lun: fake.dummy
    shared_target_ip:
!EOF!
#   sharing_backing_file: yes
```

# Execute shell
```
cd ${LIB_DIR}

#Remove the vm machine that already exists
../../cleanVM/cleanVM.py -f ${YAML_FILE}
sleep 3

./installVM.py ${YAML_FILE}
# Remove -S libvirt with sbd. Need add shared_target_lun for iscsi
./getClusterConf.py -f ${CLUSTER_FILE} -y ${YAML_FILE} -s 150 -R -S libvirt
./cpFilesToGuest.sh  ${CLUSTER_FILE} ${CONFIG_CLUSTER_DIR}
```

# Execute shell
```
#TESTSUTES
mkdir -p ${BUILD_LOG_DIR}
cd ${LIB_DIR}

cp ${YAML_FILE} ${CLUSTER_FILE} ${BUILD_LOG_DIR}
sleep 20
TESTSUITES="initCluster.py"
./runCases.py -f ${CLUSTER_FILE} -d ${BUILD_LOG_DIR} -r "$TESTSUITES"
```

# Execute shell
```
#Add virtio disk for drbd
#This feature is not committed yet
cd ${LIB_DIR}
sleep 3 
./drbd/addVirioDisk.sh ${CLUSTER_FILE} 2 "/mnt/vm/sles_nick" 1G
sleep 2 
#upgrade drbd
./drbd/upgrade-drbd.sh ${CLUSTER_FILE} "/var/log"
# sleep 30
sleep 3 
./drbd/runDRBDFilesOnGuest.sh ${CLUSTER_FILE} ${CONFIG_CLUSTER_DIR} 1
sleep 10
TESTSUITES="drbdPacemaker.py"
./runCases.py -f ${CLUSTER_FILE} -d ${BUILD_LOG_DIR} -r "$TESTSUITES"
#Rebooting
sleep 2 
./drbd/collectLogs.sh ${CLUSTER_FILE} ${BUILD_LOG_DIR}
```

# Execute shell
```
# # Prepare env of testing upstream drbd test
# cd ${LIB_DIR}
# 
# # Since the first disk is used for testing HA drbd
# # Use the second disk for drbd-test
# ./drbd/runLinbitTest.sh ${CLUSTER_FILE} ${CONFIG_CLUSTER_DIR} 2
# 
# # Get logs from master
# sleep 2
# mkdir -p ${BUILD_LOG_DIR}
# # "/drbdtest/log/*" can be replaced by "/drbdtest/log/output.log /drbdtest/log/log /drbdtest/log/Linbit-drbd-test.yml"
# ./drbd/libs/retrieveLinbitTestLog.sh ${CLUSTER_FILE} ${BUILD_LOG_DIR} "/drbdtest/log/*"
# cp ${YAML_FILE} ${CLUSTER_FILE} ${BUILD_LOG_DIR}
# 
# # Draw the junit pic
# TESTSUITES="drbdLinbitTestParser.py"
# ./runCases.py -f ${CLUSTER_FILE} -d ${BUILD_LOG_DIR} -r "$TESTSUITES"
# 
# #Copy all logs to up project
# if [ ${isCallByOther:-0} -eq 1 ]
# then
# echo "Copy logs to up project."
# mkdir -p ${UP_BUILD_LOG_DIR}
# cp -rf ${BUILD_LOG_DIR}/* ${UP_BUILD_LOG_DIR}
# fi
```

# Post-build Actions
## 	Publish Junit test result report
###		Test report XMLs
```
**/junit-*.xml
```

###		Health report amplification factor
```
1.0
```

##	Email Notification
```
nwang@suse.com
```

##	Editable Email Notification
###		Project Recipient List
```
ha-devel@suse.de
```

###		Project Reply-To List
```
$DEFAULT_REPLYTO
```

###		Content Type
```
Default content type
```

###		Default Subject
```
$DEFAULT_SUBJECT
```

###		Default Content
```
  <hr/>
  (This mail is auto delivered, please not reply！)<br/><hr/>

   ${JELLY_SCRIPT,template="template.jelly"}
```

-------------
jenkins version:
	jenkins-1.651.3-1.2.noarch
