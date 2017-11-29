#!/usr/bin/python

import commands, subprocess
import os, sys
import re
import multiprocessing
import time

from parseYAML import GET_VM_CONF
from getClusterConf import get_vm_info_list, get_interface_info 

try:
    # python3
    from urllib.request import urlopen
except:
    # python2
    from urllib import urlopen

MAX_VM_INSTALL_TIMEOUT = 1800

disk_pattern = "qcow2:%s/SUSE-HA-%s.qcow2"
backing_file_disk_pattern = "qcow2:%s/SUSE-HA-%s-base.qcow2"

default_vm_install = {'ostype': "sles11",
                     'vcpus': 1,
                     'memory': 1024,
                     'disk_size': 15360,
                     'nic': 'br0',
                     'graphics': 'cirrus'
                    }

default_res = {'sle_source': 'http://mirror.bej.suse.com/dist/install/SLP/SLE-12-SP3-Server-LATEST/x86_64/DVD1/',
              'ha_source':'http://mirror.bej.suse.com/dist/install/SLP/SLE-12-SP3-HA-LATEST/x86_64/DVD1/'
              }

default_dev = {'disk_dir':"/mnt/vm/sles_ha_auto/"
              }

default_base_dir = "/mnt/vm/sle_base"

def getSUSEVersionViaURL(repo):
    # http://mirror.suse.asia/dist/install/SLP/SLES-11-SP4-GM/x86_64/DVD1/media.1/build
    #    SLES-11-SP4-DVD-x86_64-Build1221
    # http://mirror.suse.asia/dist/install/SLP/SLE-12-SP3-Server-GM/x86_64/DVD1/media.1/build
    #    SLE-12-SP3-Server-DVD-x86_64-Build0473
    # http://mirror.suse.asia/dist/install/SLP/SLE-15-Installer-Beta2/x86_64/DVD1/media.1/media
    #    SUSE - SLE-15-Installer-DVD-x86_64-Build333.4-Media
    #    SLE-15-Installer-DVD-x86_64-Build333.4
    #    2
    # http://mirror.bej.suse.com/dist/install/SLP/openSUSE-Leap-LATEST/x86_64/DVD1/media.1/build
    #    openSUSE-Leap-42.3-DVD-x86_64-Build0331
    # http://dist.suse.de/install/SLP/openSUSE-Tumbleweed/media.1/build
    #    openSUSE-20171125-i586-x86_64-Build0001
    url_pattern = {'-11-': {'postfix' : '/media.1/build',
                            'pattern' : 'SLE(\w)-11-(SP[1-4]-)*DVD-(\w*)-Build([\w\.]+)',
                            'flavor' : 0,
                            'version' : '11',
                            'patch' : 1,
                            'arch' : 2,
                            'build' : 3
                           },
                   '-12-': {'postfix' : '/media.1/build',
                            'pattern' : 'SLE-12-(SP[1-4]-)*(\w+)-DVD-(\w*)-Build([\w\.]+)',
                            'flavor' : 1,
                            'version' : '12',
                            'patch' : 0,
                            'arch' : 2,
                            'build' : 3
                           },
                   '-15-': {'postfix' : '/media.1/media',
                            'pattern' : 'SLE-15-(SP[1-4]-)*(\w+)-DVD-(\w*)-Build([\w\.]+)',
                            'flavor' : 1,
                            'version' : '15',
                            'patch' : 0,
                            'arch' : 2,
                            'build' : 3
                           },
                   '-Leap': {'postfix' : '/media.1/build',
                            'pattern' : 'openSUSE-Leap-(\w+\.\w)-DVD-(\w+)-Build([\w\.]+)',
                            'flavor' : 'openSUSE',
                            'version' : 'Leap',
                            'patch' : 0,
                            'arch' : 1,
                            'build' : 2
                           },
                   '-Tumbleweed': {'postfix' : '/media.1/build',
                            'pattern' : 'openSUSE-(\w+)-(\w+)-(\w+)-Build([\w\.]+)',
                            'flavor' : 'openSUSE',
                            'version' : 'Tumbleweed',
                            'patch' : 0,
                            'arch' : "i586-x86_64",
                            'build' : 3
                           },
                  }

    # flavor, version, arch, build
    suse_release = {}
    lines = []

    for version in url_pattern.keys():
        if version not in repo:
            continue

        fd = urlopen(repo+url_pattern[version]['postfix'])
        lines = fd.readlines()
        fd.close()

        if len(lines) == 0:
            return suse_release

        for line in lines:
            reg = re.search(url_pattern[version]['pattern'], line)
            if reg is not None:
                #SLES-11-SP4-DVD-x86_64-Build1221
                #('S', 'SP4-', 'x86_64', '1221')
                #SLE-12-SP3-Server-DVD-x86_64-Build0473
                #('SP3-', 'Server', 'x86_64', '0473')
                #SUSE - SLE-15-Installer-DVD-x86_64-Build349.1-Media
                #(None, 'Installer', 'x86_64', '349.1')
                #openSUSE-Leap-42.3-DVD-x86_64-Build0331
                #('42.3', 'x86_64', '0331')
                #openSUSE-20171125-i586-x86_64-Build0001
                #('20171125', 'i586', 'x86_64', '0001')
                suse_release['flavor'] = reg.groups()[url_pattern[version]['flavor']]
                suse_release['version'] = url_pattern[version]['version']
                suse_release['patch'] = reg.groups()[url_pattern[version]['patch']]
                suse_release['arch'] = reg.groups()[url_pattern[version]['arch']]
                suse_release['build'] = reg.groups()[url_pattern[version]['build']]
                break
        else:
            print "Not found any pattern in url."

    if len(suse_release) == 0:
        print "Do not have any patch info. Wrong url?"
        return suse_release

    if suse_release['flavor'] == 'S':
        suse_release['flavor'] = 'Server'
    elif suse_release['flavor'] == 'D':
        suse_release['flavor'] = 'Desktop'

    if suse_release['patch'] is None:
        suse_release['patch'] = 'SP0'
    else:
       suse_release['patch'] = suse_release['patch'].strip("-")

    return suse_release

def _replaceXML(line, key, value):
    pattern = "( *<%s>).*(</%s> *)"
    m_pa = pattern % (key, key)

    result = re.match(m_pa, line)
    if result is not None:
        return "%s%s%s\n" % (result.groups()[0], value, result.groups()[1])
    else:
        return line

def installVM(VMName, disk, OSType, vcpus, memory, disk_size, source, nic, graphics, autoyast, child_fd):
    options = "--debug --os-type %s --name %s --vcpus %d --memory %d --disk %s,vda,disk,w,%d,sparse=0, --source %s --nic bridge=%s,model=virtio --graphics %s --os-settings=%s" \
              %(OSType, VMName, vcpus, memory, disk, disk_size, source, nic, graphics, autoyast)
    # TODO: Detect host OS, using virt-install in SLE12 or later
    cmd = "echo << EOF| vm-install %s%s%s" % (options, "\n\n\n\n\n\n\n", "EOF")
    print "Install command is: %s" % cmd
    ret = os.system(cmd)
    exit(ret>>8)
    #status, output = commands.getstatusoutput(cmd)
    #p = subprocess.Popen(args=["vm-install", options], \
    #    stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    #p.communicate("\n\n\n\n\n\n\n")
    #print p.wait()

def get_shared_backing_file_name(vm, devices, repo_url):
    suse = getSUSEVersionViaURL(repo_url)
    base_name = "%s-%s-%s-%s-Build%s-size%d" % (suse['flavor'], suse['version'],
                    suse['patch'], suse['arch'], suse['build'], vm['disk_size'])
    disk = backing_file_disk_pattern % (default_base_dir, base_name)
    return disk.split(':')[1]

def get_backing_file_name(vm, devices):
     vm_name = vm['name']

     if devices.has_key("disk_dir") and devices["disk_dir"] is not None:
         disk = backing_file_disk_pattern % (devices["disk_dir"], vm_name)
     else:
         disk = backing_file_disk_pattern % (default_dev["disk_dir"], vm_name)

     return disk.split(':')[1]

def find_an_exist_backing_file(base_image):
    return os.path.isfile(base_image)

def create_vms_on_backing_file(vm_list, devices, base_image):
    for i in range(len(vm_list)):
        vm = vm_list[i]
        vm, disk = parse_vm_args(vm, devices)
        disk_name = disk.split(':')[1]

        #create the new image
        print "qemu-img create -f qcow2 %s -b %s" % (disk_name, base_image)
        if os.path.exists(os.path.dirname(disk_name)) == False:
            os.makedirs(os.path.dirname(disk_name))
        os.system("qemu-img create -f qcow2 %s -b %s" % (disk_name, base_image))

        xmlfile = "%s/%s_auto.xml" % (os.path.dirname(disk_name), vm['name'])

        fill_vm_xml(vm['name'], vm['memory'], vm['memory'], vm['vcpus'], disk_name,
            'bridge', vm['nic'], xmlfile, "../confs/backing_file_template.xml")

        print "virsh define %s with name %s" % (xmlfile, vm['name'])
        os.system("virsh define %s" % xmlfile)
        os.system("virsh start %s" % vm['name'])


def prepareVMs(vm_list=[], res={}, devices={}, autoyast=""):

    if (autoyast.strip() == '') or (os.path.exists(autoyast) == False):
        os_settings = '%s/%s' % (os.getcwd(), '../confs/autoyast/autoinst-SLE11-SLE12.xml')
    else:
        os_settings = autoyast
    for key in default_res.keys():
        if res[key] is None:
            res[key] = default_res[key]

    if devices["backing_file"] or devices["sharing_backing_file"]:
        if devices["sharing_backing_file"]:
            # Get the disk_size based on the first node's configuration
            vm, _ = parse_vm_args(vm_list[0], devices)
            base_image = get_shared_backing_file_name(vm, devices, res["sle_source"])
        else:
            base_image = get_backing_file_name(vm_list[0], devices)

        if not find_an_exist_backing_file(base_image):
            # Only installed one(1st) vm as backing file
            installVMs(vm_list[:1], res, devices, autoyast, os_settings, base_image)
            if devices["sharing_backing_file"]:
                time.sleep(100)
                vm = vm_list[0]
                ipaddr, netaddr, netmask = get_interface_info(vm['nic'])
                ip_range = "%s/%d" % (ipaddr, netmask)
                get_vm_info_list(vm_list[:1], ip_range, True)
            # Destroy and undefine vm to use disk as backing file
            os.system("virsh destroy %s" % vm_list[0]['name'])
            os.system("virsh undefine %s" % vm_list[0]['name'])

        create_vms_on_backing_file(vm_list, devices, base_image)

    else:
        installVMs(vm_list, res, devices, autoyast, os_settings)

def parse_vm_args(vm, devices):
    vm_name = vm['name']

    # get value from vm config
    if vm['disk'] is not None:
        disk = vm['disk']
    elif devices.has_key("disk_dir") and devices["disk_dir"] is not None:
        disk = disk_pattern % (devices["disk_dir"], vm_name)
    else:
        disk = disk_pattern % (default_dev["disk_dir"], vm_name)

    # Should exactly the same with devices in parseYAML.py
    # Not necessary to add 'disk_dir' and 'backing_file' here
    devices_keys=('nic', 'vcpus', 'memory', 'disk_size')

    for key in default_vm_install.keys():
        if key in devices_keys:
            if vm[key] is not None:
                vm[key] = vm[key]
            elif devices.has_key(key) and devices[key] is not None:
                vm[key] = devices[key]
            else:
                vm[key] = default_vm_install[key]
            continue

        if vm[key] is None:
            vm[key] = default_vm_install[key]

    return vm, disk

def run_install_cmd(os_settings, vm_name, vm, disk, res):
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
    process = multiprocessing.Process(target=installVM,
                            args=(vm_name, disk, vm["ostype"],
                                  vm["vcpus"], vm["memory"],
                                  vm["disk_size"], res["sle_source"],
                                  vm["nic"], vm["graphics"],
                                  autoyast, child_fd),
                            name=vm_name)
    return autoyast, parent_fd, process
    
def fill_vm_xml(vmname, memory, cur_mem, vcpus, disk, network, interface, xmlfile, templatefile = "../confs/backing_file_template.xml"):
    if os.path.exists(templatefile):
        f = open(templatefile)
        content = f.read()
        f.close()
        content = content.replace("VMNAME", vmname)
        content = content.replace("MEMORY", str(1024*memory),1)
        content = content.replace("CUR_MEMORY", str(1024*cur_mem),1)
        content = content.replace("VCPUS", str(vcpus))
        content = content.replace("DISK",disk)
        content = content.replace("NETWORK_MODE", network)
        content = content.replace("INTERFACE", interface)

        f = open(xmlfile, 'w')
        f.write(content)
        f.close()

        return True

    return False

def installVMs(vm_list, res, devices, autoyast, os_settings, base_image = ""):

    exitcode = 0
    processes = {}
    for i in range(len(vm_list)):
        vm = vm_list[i]
        vm_name = vm['name']

        vm, disk = parse_vm_args(vm, devices)
        if base_image != "" :
            disk = "qcow2:" + base_image
        print "DEBUG: prepare to install virt-machine %s in disk(base:%s) %s." % ( vm['name'], base_image, disk )

        vm_list[i] = vm
        process = {}
        process["autoyast"], process["pipe"], process['process'] = run_install_cmd(os_settings, vm_name, vm, disk, res)
        processes[vm_name] = process
        process["process"].start()

    for vm in vm_list:
        vm_name = vm['name']
        processes[vm_name]["process"].join(MAX_VM_INSTALL_TIMEOUT)
        os.remove(processes[vm_name]["autoyast"])

    for vm in vm_list:
        vm_name = vm['name']
        process = processes[vm_name]["process"]

        if process.exitcode is None:
            print "process %d for installing %s timeout\n" %(process.pid, vm_name)
            exitcode = -1
        elif process.exitcode != 0:
            print "process %d for installing %s returned error %d\n" %(process.pid, vm_name, process.exitcode)
            exitcode = -2

        if exitcode != 0:
            print "the installing processes exited with %d" % (exitcode)
            for vm1 in processes.keys():
                process1 = processes[vm1]["process"]
                if process1.is_alive():
                    print "terminate process %d with vm %s" %(process1.pid, vm1)
                    process1.terminate()
            sys.exit(exitcode)

def get_config_and_install(deployfile='../confs/vm_list.yaml', autoyast=''):
    dp = GET_VM_CONF(deployfile)

    vm_list = dp.get_vms_conf()
    resource = dp.get_single_section_conf("resources")
    devices = dp.get_single_section_conf("devices")

    prepareVMs(vm_list, resource, devices, autoyast)

def usage():
    print "usage:"
    print "\t./installVM.py <yaml-conf> <autoyast>"
    print "\tDefault yaml file in '../confs/vm_list.yaml'"
    print "\t        autoyast file in '../confs/autoyast/autoinst-SLE11-SLE12.xml'"
    sys.exit(1)

if __name__ == "__main__":
    #getSUSEVersionViaURL("http://mirror.suse.asia/dist/install/SLP/SLES-11-SP4-GM/x86_64/DVD1/")
    #getSUSEVersionViaURL("http://mirror.suse.asia/dist/install/SLP/SLE-12-SP3-Server-GM/x86_64/DVD1/")
    #getSUSEVersionViaURL("http://mirror.suse.asia/dist/install/SLP/SLE-15-Installer-LATEST/x86_64/DVD1/")
    #getSUSEVersionViaURL("http://mirror.suse.asia/dist/install/SLP/SLE-16-Installer-LATEST/x86_64/DVD1/")

    if os.path.exists("/var/run/vm-install/") == False:
        os.makedirs("/var/run/vm-install/")
    os.chmod("/var/run/vm-install/", 0755)
    if len(sys.argv) > 3:
       usage()
    elif len(sys.argv) == 3:
       get_config_and_install(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 2:
       get_config_and_install(sys.argv[1])
    else:
       get_config_and_install()
