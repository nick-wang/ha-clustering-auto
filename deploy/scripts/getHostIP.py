#!/usr/bin/python3
import sys
import os
import socket
import fcntl
import struct


def get_interfaces():
    return os.listdir('/sys/class/net')

def get_ipaddr_by_interface(interface):
    ifname = interface.strip()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        #usr/include/linux/sockios.h
        ipaddr = socket.inet_ntoa(fcntl.ioctl(s.fileno(), \
                                  0x8915, \
                                  struct.pack('256s', ifname[:15].encode('utf-8')))[20:24])
        return ipaddr
    except Exception as e:
        return ''

def is_interface_existed(interface):
    return interface in get_interfaces()

def interface_filter(interface, filter):
    return interface.startswith(filter)

def get_ip_list():
    ip_dic = {}
    interfaces = get_interfaces()
    for interface in interfaces:
        interface = interface.strip()
        if interface_filter(interface, 'vnet'):
            continue
        ipaddr = get_ipaddr_by_interface(interface)

        ip_dic[interface]=ipaddr

    return ip_dic

def get_net_mask(interface):
    ifname = interface.strip()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        netmask = socket.inet_ntoa(fcntl.ioctl(s.fileno(), \
                                  0x891b, \
                                  struct.pack('256s',ifname[:15].encode('utf-8')))[20:24])
        return netmask
    except Exception as e:
        return ''

def get_netaddr(interface):
    netmask = get_net_mask(interface).split('.')
    ipaddr = get_ipaddr_by_interface(interface).split('.')

    if len(netmask) != 4 or len(ipaddr) != 4:
        return ''

    return "%d.%d.%d.%d" % (int(ipaddr[0]) & int(netmask[0]), \
                            int(ipaddr[1]) & int(netmask[1]), \
                            int(ipaddr[2]) & int(netmask[2]), \
                            int(ipaddr[3]) & int(netmask[3]))


if __name__ == "__main__":
    if len(sys.argv) == 2:
        if is_interface_existed(sys.argv[1]):
            print("The interface %s has ipaddr %s/%s" % (sys.argv[1], get_ipaddr_by_interface(sys.argv[1]), get_net_mask(sys.argv[1])))
            print("The netaddr is %s " % get_netaddr(sys.argv[1]))
        else:
            print("no such a interface %s" % sys.argv[1])
    else:
        print("the ip list is", get_ip_list())
