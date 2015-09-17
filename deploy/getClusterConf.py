#! /usr/bin/python

import subprocess
import xml.etree.ElementTree as ET
import sys, os, time

from parseYAML import GET_VM_CONF
#virsh domiflist sles12sp1-HA
#Interface  Type       Source     Model       MAC
#-------------------------------------------------------
#vnet14     bridge     br1        virtio      52:54:00:6f:e1:8c
#<host><status state="up" reason="arp-response"/>
#<address addr="147.2.208.240" addrtype="ipv4" />
#<address addr="78:AC:C0:FE:80:B2" addrtype="mac" />
#<hostnames />
#</host>

def getMacAddrs(domname):
    p = subprocess.Popen(args=["virsh", "domiflist", domname], \
        bufsize=1024, stdin=subprocess.PIPE, stdout=subprocess.PIPE, \
        stderr=subprocess.PIPE)
    (output, erroutput) = p.communicate()
    macs = output.split("\n")
    macaddrs = []
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

def get_ip_list_by_mac(vm_name_list, ip_range="147.2.207.0/24"):
    result = {}
    xml = scan_for_hosts(ip_range)

    for vm_name in vm_name_list:
        macs = getMacAddrs(vm_name)
        for mac in macs:
            ip_address = find_ip_address_for_mac_address(xml, mac)
            if (ip_address != None) and (ip_address.strip() != ""):
                result[vm_name] = (ip_address, mac)
                # Find the first ip addr is enough
                break
        else:
            result[vm_name] = ("", "")
    return result

def get_cluster_conf(subnet='207', sleep_time="0"):
    vm_list={}

    if sleep_time != "0":
        time.sleep(int(sleep_time))

    deployfile = "%s/%s" % (os.getcwd(), 'templete/vm_list.yaml')
    dp = GET_VM_CONF(deployfile)
    vm_list = dp.get_vms_conf()

    #subnet = 207 or subnet = 208
    iprange = '147.2.%s.0/24' % subnet

    num_vms = len(vm_list.keys())
    contents = "NODES=%d\n" % num_vms

    vm_info_list = get_ip_list_by_mac(vm_list.keys(), ip_range=iprange)

    i = 1
    for vm in vm_info_list.keys():
        contents += "HOSTNAME_NODE%d=%s\n" % (i, vm)
        contents += "IP_NODE%d=%s\n" % (i, vm_info_list[vm][0])
        i += 1

    iscsi = dp.get_single_section_conf("iscsi")

    target_ip = iscsi["target_ip"]
    target_lun = iscsi["target_lun"]
    if target_ip is None:
        target_ip = "147.2.207.237"
    if target_lun is None:
        target_lun = "iqn.2015-08.suse.bej.bliu:441a202b-6aa3-479f-b56f-374e2f38ba20"
    contents += "TARGET_IP=%s\n" % target_ip
    contents += "TARGET_LUN=%s\n" % target_lun

    #Write env file to "templete/cluster_conf"
    f=open('templete/cluster_conf', 'w')
    f.write(contents)
    f.close()

    print contents
    return

def usage():
    print "usage:"
    print "\t./getClusterConf.py <subnet> <sleep-time>"
    print "example:\n\t./getClusterConf.py 207 120"
    print "\tsubnet will use 147.2.*.0/24"
    sys.exit(1)

if __name__ == "__main__":
    argc = len(sys.argv)
    if argc == 1 or argc > 3:
        usage()
    elif argc == 3:
        get_cluster_conf(sys.argv[1], sys.argv[2])
    else:
        get_cluster_conf(sys.argv[1])

