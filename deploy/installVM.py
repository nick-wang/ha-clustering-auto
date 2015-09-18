#!/usr/bin/python

import commands, subprocess
import os, sys
import multiprocessing

from parseYAML import GET_VM_CONF

def installVM(VMName, disk, OSType, vcpus, memory, disk_size, source, nic, graphics, autoyast, child_fd):
    options = "--debug --os-type %s --name %s --vcpus %d --memory %d --disk %s,vda,disk,w,%d,sparse=0, --source %s --nic %s --graphics %s --os-settings=%s" \
              %(OSType, VMName, vcpus, memory, disk, disk_size, source, nic, graphics, autoyast)
    cmd = "echo << EOF| vm-install %s%s%s" % (options, "\n\n\n\n\n\n\n", "EOF")
    os.system(cmd)
    
    #status, output = commands.getstatusoutput(cmd)
    #p = subprocess.Popen(args=["vm-install", options], \
    #    stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    #p.communicate("\n\n\n\n\n\n\n")
    #print p.wait()

def installVMs(vm_list={}, res={}):
    processes = {}
    default_vm_instll = {'ostype': "sles11",
                         'vcpus': 1,
                         'memory': 1024,
                         'disk_size': 8192,
                         'nic': 'bridge=br1,model=virtio',
                         'graphics': 'cirrus'
                        }
    default_res= {'sle_source': 'http://mirror.bej.suse.com/dist/install/SLP/SLE-12-SP1-Server-LATEST/x86_64/DVD1/',
                  'ha_source':'http://mirror.bej.suse.com/dist/install/SLP/SLE-12-SP1-HA-LATEST/x86_64/DVD1/'
                 }
    os_settings = '%s/%s' % (os.getcwd(), 'templete/my_ha_inst.xml')

    for key in default_res.keys():
        if res[key] is None:
            res[key] = default_res[key]

    for vm in vm_list.keys():
        print "DEBUG: install virt-machine %s." % vm
        process = {}
        # get value from vm config
        if vm_list[vm]['disk'] is None:
            disk = "qcow2:/mnt/vm/sles_liub/sles12sp1-HA-%s.qcow2" % vm
        else:
            disk = vm_list[vm]['disk']

        for key in default_vm_instll.keys():
            if vm_list[vm][key] is None:
                vm_list[vm][key] = default_vm_instll[key]

        f = open(os_settings, 'r')
        conf_str = f.read()
        f.close()

        f = open(vm, 'w')
        f.write(conf_str.replace("HOSTNAME", vm).replace("HA_SOURCE", res['ha_source']))
        f.close()

        autoyast = vm
        parent_fd, child_fd = multiprocessing.Pipe()
        process["process"] = multiprocessing.Process(target=installVM,
                                args=(vm, disk, vm_list[vm]["ostype"],
                                      vm_list[vm]["vcpus"], vm_list[vm]["memory"],
                                      vm_list[vm]["disk_size"], res["sle_source"],
                                      vm_list[vm]["nic"], vm_list[vm]["graphics"],
                                      autoyast, child_fd),
                                name=vm)
        process["pipe"] = parent_fd
        process["autoyast"] = autoyast
        processes[vm] = process

        process["process"].start()

    for vm in vm_list.keys():
        processes[vm]["process"].join()
        os.remove(processes[vm]["autoyast"])

def get_config_and_install(deployfile='templete/vm_list.yaml'):
    dp = GET_VM_CONF(deployfile)

    vm_list = dp.get_vms_conf()
    resource = dp.get_single_section_conf("resources")

    installVMs(vm_list, resource)

def usage():
    print "usage:"
    print "\t./installVM.py <yaml-conf>"
    print "\tDefault yaml file in 'templete/vm_list.yaml'"
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 2:
        usage()
    elif len(sys.argv) == 1:
       get_config_and_install(sys.argv[1])
    else:
       get_config_and_install()

