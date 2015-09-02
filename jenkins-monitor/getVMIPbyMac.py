import subprocess
import xml.etree.ElementTree as ET
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

def get_ip_by_mac(vm_name, ip_range='147.2.208.1-253'):
    IP_RANGE = ip_range
    macs=getMacAddrs(vm_name)
    xml = scan_for_hosts(IP_RANGE)
    for mac in macs:
        MAC_ADDRESS = mac
        ip_address = find_ip_address_for_mac_address(xml, MAC_ADDRESS)
        if ip_address != None or ip_address.strip() != "":
            return ip_address, MAC_ADDRESS

#print get_ip_by_mac(vm_name="sles12sp1-HA-2-zlliu")
