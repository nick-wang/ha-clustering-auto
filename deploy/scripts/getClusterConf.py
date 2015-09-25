#! /usr/bin/python

import subprocess, getopt
import xml.etree.ElementTree as ET
import sys, os, time
from multiprocessing import Process

from parseYAML import GET_VM_CONF
from getHostIP import get_net_mask, get_netaddr, get_ipaddr_by_interface

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

def isAllIpAssigned(vm_info_list):
    for vm in vm_info_list.keys():
        if vm_info_list[vm][0] == "":
            return False
    return True

def restartGuest(name):
    print "Restart guest %s" % name
    os.system("virsh shutdown %s" % name)
    time.sleep(20)
    os.system("virsh start %s" % name)

def restartNoIpNodes(vm_info_list):
    processes = []
    for vm in vm_info_list.keys():
        if vm_info_list[vm][0] == "":
            p = Process(target=restartGuest, args=(vm, ), name=vm)
            p.start()
            processes.append(p)

    for p in processes:
        p.join()

def get_cluster_conf(sleep_time="0", configuration="../cluster_conf",
                     yaml="../confs/vm_list.yaml", recursive=False):
    vm_list={}

    if sleep_time != "0":
        time.sleep(int(sleep_time))

    dp = GET_VM_CONF(yaml)

    vm_list = dp.get_vms_conf()
    devices = dp.get_single_section_conf("devices")

    if devices is not None and devices.has_key("nic"):
        interface = devices["nic"]
    else:
        interface = "br0"
    ipaddr = get_ipaddr_by_interface(interface)
    netaddr = get_netaddr(interface)
    netmask = get_net_mask(interface).split(".")
    if len(netmask) != 4:
        netmask_int = 24
    else:
        netmask_int = 0
        for i in netmask:
            netmask_int += bin(int(i))[2:].count("1")
    ip_range = "%s/%d" % (netaddr, netmask_int)

    num_vms = len(vm_list.keys())
    contents = "NODES=%d\n" % num_vms

    print "DEBUG: Checking ip range: %s" % ip_range
    vm_names = vm_list.keys()
    vm_info_list = get_ip_list_by_mac(vm_names, ip_range)

    recur_times = 0
    already_restart = False
    while recursive:
        if isAllIpAssigned(vm_info_list):
            print "All nodes have been assigned IP address."
            break

        if recur_times == 20:
            if already_restart:
                print "Failed to get IP address!"
                sys.exit(3)
            else:
                restartNoIpNodes(vm_info_list)
                recur_times = 0
                already_restart = True

        time.sleep(10)
        recur_times += 1
        print "Checking again..."
        vm_info_list = get_ip_list_by_mac(vm_names, ip_range)

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
    contents += "NETADDR=%s\n" % netaddr
    contents += "IPADDR=%s\n" % ipaddr
    #Write env file to "../cluster_conf"
    f=open(configuration, 'w')
    f.write(contents)
    f.close()

    print contents
    return

def usage():
    print "usage:"
    print "\t./getClusterConf.py -s <sleep-time> -f <configuration> -y <yaml>"
    print "example:\n\t./getClusterConf.py -s 120 -f ../cluster_conf -y ../confs/vm_list.yaml"
    print "\tsubnet will use nic in yaml file(devices)."
    sys.exit(1)

def getOption():
    options = {"sleep": "0", "configuration": "../cluster_conf",
               "yaml": "../confs/vm_list.yaml", "recursive": False}

    try:
        opts, args = getopt.getopt(sys.argv[1:], "s:f:y:R",
                    ["sleep=", "configuration=", "yaml=", "recursive"])
    except getopt.GetoptError:
        print "Get options Error!"
        sys.exit(2)

    for opt, value in opts:
        if opt in ("-s", "--sleep"):
            options["sleep"] = value
        elif opt in ("-f", "--configuration"):
            options["configuration"] = value
        elif opt in ("-y", "--ymal"):
            options["yaml"] = value
        elif opt in ("-R", "--recursive"):
            options["recursive"] = True
        else:
            usage()

    return options

if __name__ == "__main__":
    options = getOption()
    get_cluster_conf(options["sleep"], options["configuration"],
                     options["yaml"], options["recursive"])
