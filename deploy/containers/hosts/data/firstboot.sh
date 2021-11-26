#!/bin/bash

source /data/HOSTENV
echo "Import HOST ENV:"
echo "------"
echo "HOST_IP: ${HOST_IP}"
echo "------"

# Overlap /var/lib/jenkins/jobs if jobs.tgz existed in /data
if [ -e /data/jobs.tgz ]; then
	tar -xvf /data/jobs.tgz -C /var/lib/jenkins
	chown -R jenkins: /var/lib/jenkins/jobs
fi

# Modify mail server address
echo -e "\nModify jenkinsUrl of mail address...\n/var/lib/jenkins/jenkins.model.JenkinsLocationConfiguration.xml"
echo "------"
sed -i "/jenkinsUrl/s#http://.*:8080#http://${HOST_IP}:8080#" /var/lib/jenkins/jenkins.model.JenkinsLocationConfiguration.xml
cat /var/lib/jenkins/jenkins.model.JenkinsLocationConfiguration.xml
echo -e "\n------"

# Modify mail server address
# hudson.plugins.emailext.ExtendedEmailPublisher.xml and hudson.tasks.Mailer.xml get from /app/files/jenkins/
echo -e "\nModify hudsonUrl of smtp server...\n/var/lib/jenkins/hudson.tasks.Mailer.xml"
echo "------"
sed -i "/hudsonUrl/s#http://.*:8080#http://${HOST_IP}:8080#" /var/lib/jenkins/hudson.tasks.Mailer.xml
cat /var/lib/jenkins/hudson.tasks.Mailer.xml
