#!/bin/bash

# Untar jenkins job configurations to overlap /var/lib/jenkins
# jenkins-hahost-clean.xxx.tgz didn't packaged in github.
# Need to get it from /var/lib/jenkins
# Remove all jobs/xxx/builds to save space
echo "Phase 1 Untar jenkins and change owner..."
tar xvf /app/files/jenkins-hahost-clean*.tgz -C /var/lib
# Configure mail sender SMTP, https://support.google.com/mail/answer/7126229
# mail_host="smtp.gmail.com"
# mail_port='587'
# mail_user="slehapek"
# mail_pass="sXXenXvXXl"
# mail_postfix="gmail.com"
cp -rf /app/files/jenkins/hudson* /var/lib/jenkins
chown -R jenkins: /var/lib/jenkins

echo "Phase 2 Get CI source code from gitlab..."
# Need openvpn to access suse.de
mkdir -p /var/lib/jenkins-work
git clone gitlab@gitlab.suse.de:BinLiu/ha-cluster-deploy.git /var/lib/jenkins-work/ha-share
cp /app/files/motd /etc/motd

echo "Phase 3 Configuring..."
# Make Jenkins run with root
sed -i '/^JENKINS_USER=/s/JENKINS_USER=.*/JENKINS_USER="root"/g' /etc/sysconfig/jenkins
# Email sending, https://www.edureka.co/community/68998/sslhandshakeexception-appropriate-protocol-inappropriate
sed -i '/^JENKINS_JAVA_OPTIONS=/s/JENKINS_JAVA_OPTIONS=.*/JENKINS_JAVA_OPTIONS="-Djava.awt.headless=true -Dmail.smtp.starttls.enable=true -Dmail.smtp.ssl.protocols=TLSv1.2"/g' /etc/sysconfig/jenkins

echo "Phase 4 Patching..."
# Enable the access of apache2 in /srv/www/htdocs
patch /etc/apache2/default-server.conf -p0 </app/patches/configure-apache2.patch
# Support run rcjenkins xxx in script
patch /etc/rc.status -p0 </app/patches/run-rcjenkins-in-script.patch

# start jenkins (Useless in image)
#echo "Phase 5 Starting services..."
#apachectl start # apachectl stop. apachectl -D FOREGROUND to make in the fg
#rcjenkins start # chkconfig jenkins on
