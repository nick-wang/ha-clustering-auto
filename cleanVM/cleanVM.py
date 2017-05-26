#! /usr/bin/python

import os
import sys
import commands
import time
import socket
import smtplib
import utils
import getopt
import yaml

import smtplib
from email.mime.text import MIMEText
mailto_list=["bliu@suse.com"]#, "zzhou@suse.com"]
mail_host="smtp.gmail.com"
mail_port='587'
mail_user="slehapek"
mail_pass="susenovell"
mail_postfix="gmail.com"

class Disk:
    def __init__(self, label, path, stat):
        self.label = label
        self.path = path
        self.stat = stat

    def get_label(self):
        return self.label

    def get_path(self):
        return self.path

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

    def get_vmname(self):
        return self.name

    def get_disks(self):
        return self.disks

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

def getVMByName(vmname):
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
    return vm

def remove_vm(vm, remove=True):
    vmname = vm.get_vmname()
    disk_list = vm.get_disks()
    cmd = 'virsh destroy %s' % vmname
    status, output = commands.getstatusoutput(cmd)
    print "destroying vm %s" % vmname
    #just shutdown vm
    if remove == False:
        return

    for disk in disk_list:
        path = disk.get_path()
        if os.path.exists(path) == False:
            continue
        stat_struct = os.stat(path)
        os.remove(path)
        print "os.remove(%s)" % path
    cmd = "virsh undefine %s" % vmname
    status, output = commands.getstatusoutput(cmd)
    print "status, output = commands.getstatusoutput(%s)" % cmd

def checkVMExists(vmname):
    status,_=commands.getstatusoutput("virsh domid %s" % vmname)
    if status==0:
        return True
    else:
        return False

def removeVMByName(vmname, remove=True):
    vm = getVMByName(vmname)
    remove_vm(vm, remove)

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
        vm = getVMByName(vmname)
        diff = now - vm.vm_mtime()
        if diff >= 7776000:
            delete_list.append(vm)
            remove_vm(vm)

        elif diff >= 5184000 and diff < 7776000:
            expired_list.append(vm)

    content = formatVMs(delete_list, "deleted")
    content = content + '\n' + formatVMs(expired_list, "expired") + '\n\n'
    return content

def removeVMViaYaml(yamlfile, remove=True):
    with open(yamlfile,'r') as f:
        ya = yaml.load(f)
    vms = ya.get('nodes')
    for vm in vms:
        if checkVMExists(vm["name"]):
            removeVMByName(vm["name"], remove)

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

def get_content():
    content = getHostInfo()
    ip = get_ip_first_ip()
    title = 'SLEX Lab - VM garbage collector - %s(%s) ' % (socket.gethostname(), ip)
    content = content + "("+ ip + ")\n" + getVMList()
    if os.path.exists('notice.txt'):
        f = open('notice.txt')
        content = content + f.read()
        print content
    return title, content

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

def usage():
    print '''Usage:
        To clean old vms and sendmail: ./cleanVM.py -m
        To remove specified vms: ./cleanVM.py -c "vm1 vm2"
        To remove specified vms via yaml: ./cleanVM.py -f file.yaml
        To shutdown vm instead of remove vm, please add "-s" option
          example of yaml file:
            nodes:
              - name: node-1
              - name: node-2
              - name: node-3
    '''
    sys.exit(-2)

if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:], "c:mf:s")
    remove = True
    yaml_file = None
    vm_list = None
    for opt, value in opts:
       if opt == '-m':
           title, content = get_content()
           print content
           if send_mail(mailto_list,title,content):
               print "success"
               sys.exit(0)
           else:
               print "failed"
               sys.exit(-3)
       elif opt == '-c':
           vm_list = value.split()
       elif opt == '-f':
           if os.path.exists(value) and os.path.isfile(value):
               yaml_file = value
           else:
              print "%s is not exist or not a file." % value
              sys.exit(-3)
       elif opt == "-s":
           remove = False
       else:
           print "Wrong input. opt %s, value %s" % (opt, value)
    if vm_list is not None:
        for vmname in vm_list:
            if checkVMExists(vmname):
                removeVMByName(vmname, remove)
        sys.exit(0)
    elif yaml_file is not None:
        removeVMViaYaml(yaml_file, remove)
        sys.exit(0)
    usage()
