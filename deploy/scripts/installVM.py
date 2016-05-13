#!/usr/bin/python

import commands, subprocess
import os, sys
import re
import multiprocessing

from parseYAML import GET_VM_CONF

def _replaceXML(line, key, value):
    pattern = "( *<%s>).*(</%s> *)"
    m_pa = pattern % (key, key)

    result = re.match(m_pa, line)
    if result is not None:
        return "%s%s%s\n" % (result.groups()[0], value, result.groups()[1])
    else:
        return line

def installVM(VMName, disk, OSType, vcpus, memory, disk_size, source, nic, graphics, autoyast, child_fd):
    options = "--debug --os-type %s --name %s --vcpus %d --memory %d --disk %s,vda,disk,w,%d,sparse=0, --source %s --nic %s --graphics %s --os-settings=%s" \
              %(OSType, VMName, vcpus, memory, disk, disk_size, source, nic, graphics, autoyast)
    cmd = "echo << EOF| vm-install %s%s%s" % (options, "\n\n\n\n\n\n\n", "EOF")
    print "Install command is: %s" % cmd
    os.system(cmd)
    
    #status, output = commands.getstatusoutput(cmd)
    #p = subprocess.Popen(args=["vm-install", options], \
    #    stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    #p.communicate("\n\n\n\n\n\n\n")
    #print p.wait()

def installVMs(vm_list=[], res={}, devices={}, autoyast=""):
    nic_pattern = "bridge=%s,model=virtio"
    disk_pattern = "qcow2:%s/sles12sp1-HA-%s.qcow2"

    processes = {}
    default_vm_instll = {'ostype': "sles11",
                         'vcpus': 1,
                         'memory': 1024,
                         'disk_size': 8192,
                         'nic': 'br0',
                         'graphics': 'cirrus'
                        }
    default_res = {'sle_source': 'http://mirror.bej.suse.com/dist/install/SLP/SLE-12-SP1-Server-LATEST/x86_64/DVD1/',
                  'ha_source':'http://mirror.bej.suse.com/dist/install/SLP/SLE-12-SP1-HA-LATEST/x86_64/DVD1/'
                  }
    default_dev = {'disk_dir':"/mnt/vm/sles_ha_auto/"
                  }
    if (autoyast.strip() == '') or (os.path.exists(autoyast) == False):
        os_settings = '%s/%s' % (os.getcwd(), '../confs/my_ha_inst.xml')
    else:
        os_settings = autoyast

    for key in default_res.keys():
        if res[key] is None:
            res[key] = default_res[key]

    for vm in vm_list:
        vm_name = vm['name']
        print "DEBUG: install virt-machine %s." % vm_name
        process = {}
        # get value from vm config
        if vm['disk'] is not None:
            disk = vm['disk']
        elif devices.has_key("disk_dir") and devices["disk_dir"] is not None:
            disk = disk_pattern % (devices["disk_dir"], vm_name)
        else:
            disk = disk_pattern % (default_dev["disk_dir"], vm_name)

        for key in default_vm_instll.keys():
            if key == "nic":
                if vm["nic"] is not None:
                    vm["nic"] = nic_pattern % vm["nic"]
                elif devices.has_key("nic") and devices["nic"] is not None:
                    vm["nic"] = nic_pattern % devices["nic"]
                else:
                    vm["nic"] = nic_pattern % default_vm_instll["nic"]
                continue

            if vm[key] is None:
                vm[key] = default_vm_instll[key]

        f = open(os_settings, 'r')
        conf_str = f.readlines()
        f.close()

        if not os.path.isdir("../dummy_temp"):
            os.mkdir("../dummy_temp")

        f = open("../dummy_temp/%s" % vm_name, 'w')
        for line in conf_str:
            line = _replaceXML(line, "media_url", res['ha_source'])
            line = _replaceXML(line, "hostname", vm_name)
            f.write(line)
        f.close()

        autoyast = "../dummy_temp/%s" % vm_name
        parent_fd, child_fd = multiprocessing.Pipe()
        process["process"] = multiprocessing.Process(target=installVM,
                                args=(vm_name, disk, vm["ostype"],
                                      vm["vcpus"], vm["memory"],
                                      vm["disk_size"], res["sle_source"],
                                      vm["nic"], vm["graphics"],
                                      autoyast, child_fd),
                                name=vm_name)
        process["pipe"] = parent_fd
        process["autoyast"] = autoyast
        processes[vm_name] = process

        process["process"].start()

    for vm in vm_list:
        vm_name = vm['name']
        processes[vm_name]["process"].join()
        os.remove(processes[vm_name]["autoyast"])

def get_config_and_install(deployfile='../confs/vm_list.yaml', autoyast=''):
    dp = GET_VM_CONF(deployfile)

    vm_list = dp.get_vms_conf()
    resource = dp.get_single_section_conf("resources")
    devices = dp.get_single_section_conf("devices")
    installVMs(vm_list, resource, devices, autoyast)

def usage():
    print "usage:"
    print "\t./installVM.py <yaml-conf> <autoyast>"
    print "\tDefault yaml file in '../confs/vm_list.yaml'"
    print "\t        autoyast file in '../confs/my_ha_inst.xml'"
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 3:
        usage()
    elif len(sys.argv) == 3:
       get_config_and_install(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 2:
       get_config_and_install(sys.argv[1])
    else:
       get_config_and_install()

