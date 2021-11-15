#!/bin/bash

source /data/HOSTENV
echo "Import HOST ENV:"
echo "------"
echo "HOST_IP: ${HOST_IP}"
echo "------"

# Modify mail server address
echo -e "\nModify jenkinsUrl of mail address...\n/var/lib/jenkins/jenkins.model.JenkinsLocationConfiguration.xml"
echo "------"
sed -i "/jenkinsUrl/s#http://.*:8080#http://${HOST_IP}:8080#" /var/lib/jenkins/jenkins.model.JenkinsLocationConfiguration.xml
cat /var/lib/jenkins/jenkins.model.JenkinsLocationConfiguration.xml
echo -e "\n------"
