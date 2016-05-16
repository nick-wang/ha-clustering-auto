#!/usr/bin/python

import os, getopt, sys
sys.path.append(os.path.dirname(os.getcwd())+"/scripts")
from parseYAML import GET_VM_CONF
from getHostIP import *

sys.path.append('../')

def getCtsConf(stonith_type="external/libvirt", interface1='br1', configuration="../cts_conf", yamlfile='../confs/vm_list.yaml'):
    dp = GET_VM_CONF(yamlfile)
    content=""
    
    vm_list = dp.get_vms_conf()
    node_list=""
    for vm in vm_list:
        if node_list == '':
            node_list = vm['name']
        else:
            node_list += ',' + vm['name']
    f = open(configuration, 'w')
    host_ip=get_ipaddr_by_interface(interface = interface1)
    content += "NODE_LIST=%s\n" % node_list
    content += "STONITH_TYPE=%s\n" % stonith_type
    content += "HOST_IP=%s\n" % host_ip
    f.write(content)
    f.close()

def getOption():
    options = {"interface": "br1", "stonith_type": "external/libvirt", "configuration": "../cts_conf", "yamlfile": "../confs/vm_list.yaml"}

    try:
        opts, args = getopt.getopt(sys.argv[1:], "i:s:f:y:", ["interface=", "stonith_type=", "configuration=", "yamlfile="])
    except getopt.GetoptError:
        print "Get options Error!"
        sys.exit(1)

    for opt, value in opts:
        if opt in ("-i", "--interface"):
            options["interface"] = value
        elif opt in ("-s", "--stonith_type"):
            options["sleep"] = value
        elif opt in ("-f", "--configuration"):
            options["configuration"] = value
        elif opt in ("-y","--yamlfile"):
            options["yamlfile"] = value
        else:
            usage()

    return options

if __name__ == "__main__":
    options = getOption()
    getCtsConf(options["stonith_type"], options["interface"], options["configuration"], options["yamlfile"])
