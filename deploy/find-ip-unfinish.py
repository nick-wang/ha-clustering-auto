#! /usr/bin/python

# Originally from scripts/getClusterConf.py

import subprocess, getopt
import xml.etree.ElementTree as ET
import sys, os, time

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

def get_ip_list_by_mac(vm_name, ip_range="10.67.16.0/21"):
    result = {}
    xml = scan_for_hosts(ip_range)

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

def show_ip(node, iprange):
    print get_ip_list_by_mac(node, iprange)

def usage():
    print "usage:"
    print "\t./find-ip.py -n <node_name> -r <ip_range>"
    print "example:\n\t./find-ip.py -n node1 -f 10.67.16.0/21"
    print "\tsubnet will use nic in yaml file(devices)."
    sys.exit(1)

def getOption():
    options = {"node": "", "iprange": "10.67.16.0/21"}

    try:
        opts, args = getopt.getopt(sys.argv[1:], "n:r",
                    ["node=", "iprange="])
    except getopt.GetoptError:
        print "Get options Error!"
        sys.exit(2)
    for opt, value in opts:
        if opt in ("-n", "--node"):
            options["node"] = value
        elif opt in ("-r", "--iprange"):
            options["iprange"] = value
        else:
            usage()

    return options

if __name__ == "__main__":
    options = getOption()
    show_ip(options["node"], options["iprange"])
