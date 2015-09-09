#! /usr/bin/python
import subprocess
import yaml
import xml.etree.ElementTree as ET
import sys
import os
#virsh domiflist sles12sp1-HA
#Interface  Type       Source     Model       MAC
#-------------------------------------------------------
#vnet14     bridge     br1        virtio      52:54:00:6f:e1:8c
#<host><status state="up" reason="arp-response"/>
#<address addr="147.2.208.240" addrtype="ipv4" />
#<address addr="78:AC:C0:FE:80:B2" addrtype="mac" />
#<hostnames />
#</host>

'''
nodes:
- name: node01
  mac: 00:0C:29:6B:CA:02
  disk: qcow2:/mnt/vm/sles_liub/sles12sp1-HA-liubin_node01.qcow2
  ostype: sles11
  vcpus: 2
  memory: 1024
  disk_size: 8192
  source:
  nic:
  graphics:
  os_settings:

- name: node02
  mac: 00:0C:29:C9:21:D5
  disk: qcow2:/mnt/vm/sles_liub/sles12sp1-HA-liubin_node02.qcow2
  ostype: sles11
  vcpus: 2
  memory: 1024
  disk_size: 8192
  source:
  nic:
  graphics:
  os_settings:  

- name: node03
  mac: 00:0C:29:D7:4C:31
  disk: qcow2:/mnt/vm/sles_liub/sles12sp1-HA-liubin_node03.qcow2
  ostype: sles11
  vcpus: 2
  memory: 1024
  disk_size: 8192
  source:
  nic:
  graphics:
  os_settings:

storage:
  target_ip: 147.2.207.237
  target_lun: iqn.2015-08.suse.bej.bliu:441a202b-6aa3-479f-b56f-374e2f38ba20
'''
class GET_VM_CONF:
    def __init__(self, url):
        self.ya = self.get_yaml(url)

    def get_yaml(self, url):
        """
            Get group infomation from client.yaml
        """
        with open(url,'r') as f:
            ya = yaml.load(f)
        return ya
    def get_iscsi_conf(self):
        storage = self.ya.get('storage')
        return storage.get('target_ip'), storage.get('target_lun')

    def get_vms_conf(self):
        vms = {}
        nodes = self.ya.get('nodes')
        for node in nodes:
            vm = self.store_vm_conf(node)

            if not vms.has_key(vm['name']):
                vms[vm['name']] = vm
            else:
                print "Error! Duplicate node name(%s) detected." % vm['name']
                sys.exit(2)
        return vms

    def store_vm_conf(self, master):
        vm = {}
        vm['name'] = master.get('name')
        vm['mac'] = master.get('mac')
        vm['ostype'] = master.get('ostype')
        vm['disk'] = master.get('disk')
        vm['vcpus'] = master.get('vcpus')
        vm['memory'] = master.get('memory')
        vm['disk_size'] = master.get('disk_size')
        vm['source'] = master.get('source')
        vm['nic'] = master.get('nic')
        vm['graphics'] = master.get('graphics')
        vm['os_settings'] = master.get('os_settings')
        return vm

def getMacAddrs(domname):
    p = subprocess.Popen(args=["virsh", "domiflist", domname], \
        bufsize=1024, stdin=subprocess.PIPE, stdout=subprocess.PIPE, \
        stderr=subprocess.PIPE)
    (output, erroutput) = p.communicate()
    macs=output.split("\n")
    macaddrs=[]
    for mac in macs:
        if ("Interface" in mac) or \
           ("-------------------" in mac) or\
           mac == '':
            continue
        macaddrs.append(mac.split()[-1])
    return macaddrs

def scan_for_hosts(ip_range):
    """Scan the given IP address range using Nmap and return the result
    in XML format.
    """
    nmap_args = ['nmap', '-n', '-sP', '-oX', '-', ip_range]
    p=subprocess.Popen(nmap_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdoutput, stderroutput=p.communicate()
    return stdoutput

def find_ip_address_for_mac_address(xml, mac_address):
    """Parse Nmap's XML output, find the host element with the given
    MAC address, and return that host's IP address.
    """
    ipaddr=""
    mac=""
    root = ET.fromstring(xml)
    for host in root.findall('host'):
        addr_list = host.findall('address')
        if len(addr_list) < 2:
            continue
        for addr in addr_list:
            if addr.get("addrtype") == 'ipv4':
                ipv4 = addr.get('addr')
            elif addr.get('addrtype') == 'mac':
                mac = addr.get('addr')
        if mac.lower() == mac_address.lower():
            return ipv4

def get_address_of_type(host_elem, type_):
    """Return the host's address of the given type."""
    return host_elem.find('./address[@addrtype="%s"]' % type_).get('addr')

def get_ip_by_mac(vm_name, ip_range='147.2.207.1-253'):
    IP_RANGE = ip_range
    macs=getMacAddrs(vm_name)
    xml = scan_for_hosts(IP_RANGE)
    for mac in macs:
        MAC_ADDRESS = mac
        ip_address = find_ip_address_for_mac_address(xml, MAC_ADDRESS)
        if (ip_address != None) and (ip_address.strip() != ""):
            return ip_address, MAC_ADDRESS, vm_name
    return ("","", vm_name)

def write_cluster_conf(iprange='147.2.207.1-253'):
    vm_list={}
    deployfile = "%s/%s" % (os.getcwd(), 'templete/vm_list.yaml')
    dp = GET_VM_CONF(deployfile)
    vm_list = dp.get_vms_conf()

    #os.sleep(20)
    #ip_range_list = ['147.2.207.1-253', '147.2.208.1-253']
    i = 1
    num_vms = len(vm_list.keys())
    contents = "NODES=%d\n" % num_vms
    #for ip_range1 in ip_range_list:
    for vm_name1 in vm_list.keys():
        ip, mac, vm_name = get_ip_by_mac(vm_name=vm_name1, ip_range=iprange)
        #if ip == "":
        #    continue
        contents = contents + "HOSTNAME_NODE%d=%s\n" % ( i, vm_name )
        contents = contents + "IP_NODE%d=%s\n" % (i, ip)
        i = i + 1
    #installVM(VMName="sles12sp1-HA-liubin", OSType="sles11",disk="qcow2:/mnt/vm/sles_liub/sles12sp1-HA-liubin.qcow2")
    target_ip, target_lun = dp.get_iscsi_conf()
    if target_ip is None:
        target_ip = "147.2.207.237"
    if target_lun is None:
        target_lun = "iqn.2015-08.suse.bej.bliu:441a202b-6aa3-479f-b56f-374e2f38ba20"
    contents = contents + "TARGET_IP=%s\n" % target_ip
    contents = contents + "TARGET_LUN=%s\n" % target_lun
    f=open('cluster_conf', 'w')
    f.write(contents)
    f.close()
    return contents


def usage():
    print "usage:"
    print "\t./getIPByName.py getIPByName vm_name ip_range"
    print "\t./getIPByName.py writeClusterConf"
    print "example:\n\t./getIPByName.py getIPByName sles12-HA 147.2.207.1-253"
    sys.exit(1)

if __name__ == "__main__":
    if sys.argv[1] == "getIPByName":
        print get_ip_by_mac(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "writeClusterConf":
        print write_cluster_conf()
    else:
        usage()
