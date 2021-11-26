# Build jenkins-ci
# git@github.com:nick-wang/ha-clustering-auto.git

FROM opensuse/leap:15.3

WORKDIR /app

COPY ./app/ /app

# Deploy ssh keys for HA-x connection and gitlab repo
RUN mkdir /root/.ssh
COPY ./app/files/.ssh /root/.ssh
RUN chmod 0600 /root/.ssh/authorized_keys /root/.ssh/id_rsa

# Jenkins rpm repo
RUN zypper ar -Gf https://pkg.jenkins.io/opensuse-stable/ jenkins

# sysvinit-tools for /sbin/checkproc -> rcjenkins
# dejavu-fonts for showing jenkins pages
RUN zypper -n install java-11-openjdk java-11-openjdk-headless jenkins=1.651.3-1.2 sysvinit-tools dejavu-fonts

# openssh-clients for ssh command used by jenkins
# wget, python3 for download_iso.py
RUN zypper -n install git-core tar gzip apache2 patch openssh-clients python3 wget

# iputils/iproute2 for ping/ip to debug network
RUN zypper -n install less man vim lvm2 iputils iproute2 bash-completion

# EXPOSE 80
EXPOSE 8080

RUN /app/prepare-in-build.sh

# Firsh boot
CMD /data/firstboot.sh
