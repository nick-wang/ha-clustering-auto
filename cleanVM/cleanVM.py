#! /usr/bin/python

import os
import sys
import commands
import time
import socket
import smtplib
import utils

class Disk:
    def __init__(self, label, path, stat):
        self.label = label
        self.path = path
        self.stat = stat

class VM:
    def __init__(self, name, disks=[]):
        self.name = name
        self.disks = []

    def adddisk(self, disk):
        self.disks.append(disk)

    def removedisk(self, disk):
        self.disks.pop(disk)

    def vm_mtime(self):
        self.lastmodified = 0
        for disk in self.disks:
            if self.lastmodified < disk.stat.st_mtime:
                self.lastmodified = disk.stat.st_mtime
        return self.lastmodified

def canCleanVMs(pathname="/mnt/vm/"):
	avail = utils.get_fs_freespace(pathname)
	return avail < 1 - 0.6

def formatVMs(vmlist, listname):
    content = '\n\tVMs are %s:' % listname
    for vm in vmlist:
        content = content + '\n\t\t%s:' % vm.name
        for disk in vm.disks:
            #content = content + '\n\t\t\t%s\t%s\t\t\t%s' % (disk.label, disk.path, time.asctime(time.localtime(disk.stat.st_mtime)))
            content = content + '\n\t\t\t%s\t%s\t\t\t%s' % (disk.label, disk.path, time.strftime("%Y-%m-%d", time.localtime(disk.stat.st_mtime)))
    return content

def printVMs(vmlist, listname):
    print '\tVMs are %s:' % listname
    for vm in vmlist:
        print '\t\t%s:' % vm.name
        for disk in vm.disks:
            print '\t\t\t%s\t%s\t\t\t%s' % (disk.label, disk.path, time.asctime(time.localtime(disk.stat.st_mtime)))
    
def getVMList():
    cmd='virsh list --all|grep "shut off"'
    status, output=commands.getstatusoutput(cmd)
    elelist=output.split('\n')
    expired_list=[]
    delete_list=[]
    now = time.time()
    diff = 0
    if canCleanVMs() == False:
		sys.exit(-1)
    for el in elelist:
        vmname = el[7:][:-8].strip()
        cmd = 'virsh domblklist %s|grep \/' % (vmname)
        status, output = commands.getstatusoutput(cmd)
        if status:
            sys.exit(-1)
        disk_list = output.split('\n')
        expired = False
        delete = False
        vm = VM(vmname)
        for disk in disk_list:
            label, path = disk.strip().split()
            if os.path.exists(path) == False:
                continue
            stat_struct = os.stat(path)
            disk1 = Disk(label, path, stat_struct)
            vm.adddisk(disk1)
        diff = now - vm.vm_mtime()
        #print vm.name, time.asctime(time.localtime(vm.lastmodified))
        if diff >= 7776000:
            delete_list.append(vm)
            for disk in disk_list:
                path1 = disk.strip().split()[-1]
                if os.path.exists(path1) == False:
                    continue
                os.remove(path1)
                print "os.remove(%s)" % path1
            cmd = "virsh undefine %s" % vmname
            status, output = commands.getstatusoutput(cmd)
            print "status, output = commands.getstatusoutput(%s)" % cmd
            
        elif diff >= 5184000 and diff < 7776000:
            expired_list.append(vm)

    content = formatVMs(delete_list, "deleted")
    content = content + '\n' + formatVMs(expired_list, "expired") + '\n\n' 
    return content

def getHostInfo():
    hostname = socket.gethostname()
    #ip = socket.gethostbyname(hostname)
    #print '\tThe host is (%s/%s) ' %(hostname, ip)
    return 'On Host %s' %(hostname)

def get_ip_first_ip():
    cmd = 'ip addr|grep -w inet|egrep -v "vir|127.0.0.1"'
    status,output = commands.getstatusoutput(cmd)
    ipList=output.split('\n')
    return ipList[0].strip().split()[1]

content = getHostInfo()
ip = get_ip_first_ip()
title = 'SLEX Lab - VM garbage collector - %s(%s) ' % (socket.gethostname(), ip)
content = content + "("+ ip + ")\n" + getVMList()
if os.path.exists('notice.txt'):
    f = open('notice.txt')
    content = content + f.read()
print content

import smtplib
from email.mime.text import MIMEText
mailto_list=["bliu@suse.com"]#, "zzhou@suse.com"]
mail_host="smtp.gmail.com"
mail_port='587'
mail_user="slehapek"
mail_pass="susenovell"
mail_postfix="gmail.com"
 
def send_mail(to_list,sub,content):
    me="slehapek"+"<"+mail_user+"@"+mail_postfix+">"
    msg = MIMEText(content,_subtype='plain',_charset='gb2312')
    msg['Subject'] = sub
    msg['From'] = me
    msg['To'] = ";".join(to_list)
    try:
        s = smtplib.SMTP(mail_host, mail_port)
        #s.ehlo()
        s.starttls()
        s.login(mail_user,mail_pass)
        s.sendmail(me, to_list, msg.as_string())
        s.close()
        return True
    except Exception, e:
        print str(e)
        return False

if __name__ == '__main__':
    if send_mail(mailto_list,title,content):
        print "success"
    else: 
        print "failed"
