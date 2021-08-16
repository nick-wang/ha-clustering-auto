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

# Remove autoyast file after installation
clean_up = True

# Enable/disable debug log
DEBUG = False

# Legacy vm-install will be removed, replace to virt-install
# virt-install require nfs/http/formatted disk to attach for autoyast file
# virt-install only support graphics vnc. vm-install can use cirrus
# TODO: Detect host OS, using virt-install in SLE12 or later
VIRT_INSTALL = True

# Maximum VM installation time
MAX_VM_INSTALL_TIMEOUT = 3600

# Internal:
# Check mirror.suse.asia/dist/slp to see whether modules/products are saved seperately
seperate = False

if VIRT_INSTALL:
    import createAutoyastDisk
    disk_pattern = "%s/SUSE-HA-%s.qcow2"
else:
    disk_pattern = "qcow2:%s/SUSE-HA-%s.qcow2"
backing_file_disk_pattern = "qcow2:%s/SUSE-HA-%s-base.qcow2"

default_base_dir = "/mnt/vm/sle_base"
dummy_folder = "../dummy_temp/"

default_vm_install = {'ostype': "sles12",
                     'vcpus': 1,
                     'memory': 1024,
                     'disk_size': 20480,
                     'nic': 'br0',
                     'second_nic': '',
                     'graphics': 'vnc'
                    }

default_res = {'sle_source': 'http://mirror.bej.suse.com/dist/install/SLP/SLE-12-SP3-Server-LATEST/x86_64/DVD1/',
              'ha_source':'http://mirror.bej.suse.com/dist/install/SLP/SLE-12-SP3-HA-LATEST/x86_64/DVD1/'
              }

default_dev = {'disk_dir':"/mnt/vm/sles_ha_auto/"
              }

autoyast_dic = { "openSUSE": {"Full_tw_outdate": "autoinst-openSUSE_tumbleweed-full.xml",
                              "Leap": "autoinst-openSUSE_leap.xml",
                              "Tumbleweed": "autoinst-openSUSE_tumbleweed.xml",
                             },
                "SLE": {"SLE11_12": "autoinst-SLE11-SLE12.xml",
                        "SLE15SP0_v1": "autoinst-SLE15-beta5.xml",
                        "SLE15SP0_v2": "autoinst-SLE15.xml",
                        "SLE15SP1_v1": "autoinst-SLE15SP1.xml",
                        "SLE15SP1_SP2_sep": "autoinst-SLE15SP1-sep-modules.xml",
                        }
               }
latest_openSUSE_autoyast = autoyast_dic['openSUSE']["Tumbleweed"]
latest_SLE_autoyast = autoyast_dic['SLE']['SLE15SP1_SP2_sep']


def getSUSEVersionViaURL(repo):
    # http://mirror.suse.asia/dist/install/SLP/SLES-11-SP4-GM/x86_64/DVD1/media.1/build
    #    SLES-11-SP4-DVD-x86_64-Build1221
    # http://mirror.suse.asia/dist/install/SLP/SLE-12-SP3-Server-GM/x86_64/DVD1/media.1/build
    #    SLE-12-SP3-Server-DVD-x86_64-Build0473
    # http://mirror.suse.asia/dist/install/SLP/SLE-15-Installer-Beta2/x86_64/DVD1/media.1/media
    #    SUSE - SLE-15-Installer-DVD-x86_64-Build333.4-Media
    #    SLE-15-Installer-DVD-x86_64-Build333.4
    #    2
    # http://mirror.suse.asia/dist/install/SLP/SLE-15-SP2-Full-Beta1/x86_64/DVD1//media.1/media
    #    SUSE - SLE-15-SP2-Full-x86_64-Build101.1-Media
    #    SLE-15-SP2-Full-x86_64-Build101.1
    #    1
    # (obsolete - no build file) http://mirror.bej.suse.com/dist/install/SLP/openSUSE-Leap-LATEST/x86_64/DVD1/media.1/build
    #    openSUSE-Leap-42.3-DVD-x86_64-Build0331
    # (obsolete - no build file) http://dist.suse.de/install/SLP/openSUSE-Tumbleweed/media.1/build
    #    openSUSE-20171125-i586-x86_64-Build0001
	# http://mirror.bej.suse.com/dist/install/SLP/openSUSE-Leap-LATEST/x86_64/DVD1/media.1/media
    #    openSUSE-Leap-15.0-DVD-x86_64-Build267.2
    # http://dist.suse.de/install/SLP/openSUSE-Tumbleweed/media.1/media
    #    openSUSE-20180812-i586-x86_64-Build435.1
    url_pattern = {'-11-': {'postfix' : '/media.1/build',
                            'pattern' : 'SLE(\w)-11-(SP[1-4]-)*DVD-(\w*)-Build([\w\.]+)',
                            'flavor' : 0,
                            'version' : '11',
                            'patch' : 1,
                            'arch' : 2,
                            'build' : 3
                           },
                   '-12-': {'postfix' : '/media.1/build',
                            'pattern' : 'SLE-12-(SP[1-5]-)*(\w+)-DVD-(\w*)-Build([\w\.]+)',
                            'flavor' : 1,
                            'version' : '12',
                            'patch' : 0,
                            'arch' : 2,
                            'build' : 3
                           },
                   '-15-': {'postfix' : '/media.1/media',
                            'pattern' : 'SLE-15-(SP[1-4])*-*(\w+)*(-DVD|-OnlineOnly)*-(\w*)-Build([\w\.]+)',
                            'flavor' : 1,
                            'version' : '15',
                            'patch' : 0,
                            'arch' : 3,
                            'build' : 4
                           },
                   'Leap': {'postfix' : '/media.1/media',
                            'pattern' : 'openSUSE-Leap-(\w+\.\w)-DVD-(\w+)-Build([\w\.]+)',
                            'flavor' : 'openSUSE',
                            'version' : 'Leap',
                            'patch' : 0,
                            'arch' : 1,
                            'build' : 2
                           },
                   'Tumbleweed': {'postfix' : '/media.1/media',
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

        print("From url: %s" %  repo+url_pattern[version]['postfix'])
        fd = urlopen(repo+url_pattern[version]['postfix'])
        lines = fd.readlines()
        fd.close()

        if len(lines) == 0:
            return suse_release

        for line in lines:
            reg = re.search(url_pattern[version]['pattern'], line)
            if reg is not None:
                print "Pattern matched: %s" % line
                print(reg.groups())

                #SLES-11-SP4-DVD-x86_64-Build1221
                #('S', 'SP4-', 'x86_64', '1221')
                #SLE-12-SP3-Server-DVD-x86_64-Build0473
                #('SP3-', 'Server', 'x86_64', '0473')
                #SUSE - SLE-15-Installer-DVD-x86_64-Build349.1-Media
                #(None, 'Installer', 'x86_64', '349.1')
                #SLE-15-SP2-Full-x86_64-Build101.1
                #('SP2-', 'Full', 'x86_64', '101.1')
                #openSUSE-Leap-42.3-DVD-x86_64-Build0331
                #('42.3', 'x86_64', '0331')
                #openSUSE-20171125-i586-x86_64-Build0001
                #('20171125', 'i586', 'x86_64', '0001')
                try:
                    suse_release['flavor'] = reg.groups()[url_pattern[version]['flavor']]
                except TypeError:
                    suse_release['flavor'] = url_pattern[version]['flavor']
                suse_release['version'] = url_pattern[version]['version']
                suse_release['patch'] = reg.groups()[url_pattern[version]['patch']]
                try:
                    suse_release['arch'] = reg.groups()[url_pattern[version]['arch']]
                except TypeError:
                    suse_release['arch'] = url_pattern[version]['arch']
                suse_release['build'] = reg.groups()[url_pattern[version]['build']]

                if "-OnlineOnly" in line:
                    print "Using OnlineOnly installer, may not work!"

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

    print(suse_release)
    return suse_release

def _replaceXML(line, key, value):
    pattern = "( *<%s>).*(</%s> *)"
    m_pa = pattern % (key, key)

    result = re.match(m_pa, line)
    if result is not None:
        return "%s%s%s\n" % (result.groups()[0], value, result.groups()[1])
    else:
        return line

def _replaceMediaURL(line, value):
    pattern = "( *<media_url>)(.*)(</media_url> *)"
    result = re.match(pattern, line)
    if result is not None:
        if "-Full-" in value:
            #since sle15 sp2 alpha6, the moudles/packages are moved to installer repo. Then combine to a "Full" repo
            #line(value) like:   http://mirror.suse.asia/dist/install/SLP/SLE-15-SP2-Full-Beta1/x86_64/DVD1/
            #result.groups()[1] like:  Module-Basesystem
            #output like:  http://mirror.suse.asia/dist/install/SLP/SLE-15-SP2-Full-Beta1/x86_64/DVD1/Module-Basesystem
            newURL = value + "/" + result.groups()[1]
        else:
            #line(value) like:   http://mirror.suse.asia/dist/install/SLP/SLE-15-SP1-Packages-Beta1/x86_64/DVD1/
            #result.groups()[1] like:  Module-Basesystem
            #output like:  http://mirror.suse.asia/dist/install/SLP/SLE-15-SP1-Module-Basesystem-Beta1/x86_64/DVD1/
            newURL = value.replace("-Packages-", "-"+result.groups()[1]+"-")
        return "%s%s%s\n" % (result.groups()[0], newURL, result.groups()[2])
    else:
        return line

def installVM(VMName, disk, OSType, vcpus, memory, disk_size, source, nic, second_nic, graphics, extra_args, autoyast, child_fd):
    if second_nic and second_nic != '':
        if VIRT_INSTALL:
            nic2 = ' --network bridge=%s ' % (second_nic)
        else:
            nic2 = ' --nic bridge=%s,model=virtio ' % (second_nic)
    else:
        nic2 = ''

    if DEBUG:
        verbose = "--debug"
    else:
        verbose = ""

    if VIRT_INSTALL:
        # Create qemu image with autoyast file
        autoyast_path = os.path.dirname(disk) + "/" + "/autoyast-img"
        autoyast_disk = createAutoyastDisk.AutoyastDisk(VMName, autoyast_path)
        autoyast_disk.save_autoyast_to_image(autoyast)

        if autoyast_disk.get_img() == "":
            print("ERROR! Failed to create qemu image with autoyast file in!")
            exit(-1)

        # Update/valid parameters like disk, disk_size, graphics
        size = int(disk_size)/1024

        if graphics not in ("vnc", "none"):
            graphics = "vnc"

        options = "%s --wait -1 \
                --name %s --os-type %s \
                --connect qemu:///system \
                --vcpus=%d --ram=%d \
                --graphics %s \
                --noautoconsole \
                --disk path=%s,size=%d \
                --disk path=%s \
                --network bridge=%s %s \
                --watchdog i6300esb,action=reset \
                --location=%s \
                -x \"YAST_SKIP_XML_VALIDATION=1 autoyast=device://vdb/%s\"\
                " % (verbose, VMName, OSType, vcpus, memory, graphics, disk,
                        size, autoyast_disk.get_img(), nic, nic2,
                        source, createAutoyastDisk.AUTOYAST_FILENAME)
        if DEBUG:
            cmd = "virt-install %s" % options
        else:
            cmd = "virt-install %s 2>/dev/null" % options
    else:
        options = "%s --os-type %s --name %s \
                --vcpus %d --memory %d \
                --disk %s,vda,disk,w,%d,sparse=0, \
                --source %s \
                --nic bridge=%s,model=virtio %s \
                --graphics %s \
                --extra-args %s \
                --os-settings=%s" \
                  %(verbose, OSType, VMName, vcpus, memory, disk, disk_size,
                          source, nic, nic2, graphics, extra_args, autoyast)
        cmd = "echo << EOF| vm-install %s%s%s" % (options, "\n\n\n\n\n\n\n", "EOF")

    print "Install command is: %s" % cmd
    ret = os.system(cmd)
    exit(ret>>8)

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

def get_autoyast_openSUSE(suse, autoyast):
    if suse['version'] == 'Leap':
        filename = autoyast['Leap']
    # Outdate: all packages in one repo
    # Pattern matched: openSUSE - openSUSE-20191206-i586-x86_64-Build1878.2-Media
    # {'flavor': 'openSUSE', 'version': 'Tumbleweed', 'arch': 'i586-x86_64',
    # 'build': '1878.2', 'patch': '20191206'}
    elif suse['version'] == 'Tumbleweed' and suse['patch'] != 'Tumbleweed':
        filename = autoyast['Full_tw_outdate']
    # Pattern matched: openSUSE - openSUSE-Tumbleweed-DVD-x86_64-Build2147.2-Media
    else:
        filename = latest_openSUSE_autoyast

    return filename

def get_autoyast_SLE(suse, autoyast):
    global seperate

    if suse['version'] == '11' or suse['version'] == '12':
        filename = autoyast['SLE11_12']
    elif suse['version'] == '15' and suse['patch'] == 'SP0':
        if int(suse['build'].split(".")[0]) < 438:
            filename = autoyast['SLE15SP0_v1']
        else:
            filename = autoyast['SLE15SP0_v2']
    elif suse['version'] == '15'and suse['patch'] == 'SP1':
        if int(suse['build'].split(".")[0]) < 125:
            filename = autoyast['SLE15SP1_v1']
        else:
            # Since beta1, modules seperate from packages
            # eg: original repo:
            #   http://mirror.suse.asia/dist/install/SLP/SLE-15-Packages-LATEST/x86_64/DVD1/Module-Basesystem/
            # new:
            #   http://mirror.suse.asia/dist/install/SLP/SLE-15-SP1-Module-Basesystem-LATEST/x86_64/DVD1/
            seperate = True
            filename = autoyast['SLE15SP1_SP2_sep']
    elif suse['version'] == '15'and suse['patch'] == 'SP2':
            seperate = True
            filename = autoyast['SLE15SP1_SP2_sep']
    else:
        # Need set seperate for modules based autoyast
        seperate = True
        filename = latest_SLE_autoyast

    return filename

def find_autoyast_file(url):
    suse = getSUSEVersionViaURL(url)

    abspath = '%s/%s' % (os.getcwd(), '../confs/autoyast/')

    if suse['flavor'] == 'openSUSE':
        filename = get_autoyast_openSUSE(suse, autoyast_dic["openSUSE"])
    else:
        filename = get_autoyast_SLE(suse, autoyast_dic["SLE"])

    return abspath + filename

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

def create_base_image_git_entry(base_image):
    if not os.path.isfile(base_image):
		return False

    lines = os.popen("git rev-parse HEAD").readlines()
    commit = lines[0].strip()

    fd = open("%s/baseimage-git-db" % dummy_folder, "a")
    fd.write(base_image+":\t"+commit+"\n")
    fd.close()

def prepareVMs(vm_list=[], res={}, devices={}, autoyast=""):
    if (autoyast.strip() == '') or (os.path.exists(autoyast) == False):
        os_settings = find_autoyast_file(res["sle_source"])
    else:
        os_settings = autoyast

    print("Autoyast template from: %s\n" % os_settings)

    for key in default_res.keys():
        if res[key] is None:
            res[key] = default_res[key]

    if devices["backing_file"] or devices["sharing_backing_file"]:
        if devices["sharing_backing_file"]:
            # Get the disk_size based on the first node's configuration
            vm, _ = parse_vm_args(vm_list[0], devices)
            base_image = get_shared_backing_file_name(vm, devices, res["sle_source"])
        else: #"backing_file" won't share with others, also won't be tracked by cleanVM.py
            base_image = get_backing_file_name(vm_list[0], devices)

        print "Using base image: %s" % base_image

        if not find_an_exist_backing_file(base_image):
            # Only installed one(1st) vm as backing file
            installVMs(vm_list[:1], res, devices, autoyast, os_settings, base_image)
            if devices["sharing_backing_file"]:
                time.sleep(100)
                vm = vm_list[0]
                ipaddr, netaddr, netmask = get_interface_info(vm['nic'])
                ip_range = "%s/%d" % (ipaddr, netmask)
                get_vm_info_list(vm_list[:1], ip_range, True)

            create_base_image_git_entry(base_image)

            # Destroy and undefine vm to use disk as backing file
            time.sleep(50)
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
    devices_keys=('ostype', 'nic', 'second_nic', 'vcpus', 'memory', 'disk_size')

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

    if not os.path.isdir(dummy_folder):
        os.mkdir(dummy_folder)

    f = open("%s/%s" % (dummy_folder, vm_name), 'w')
    for line in conf_str:
        if not seperate:
            line = _replaceXML(line, "media_url", res['ha_source'])
        else:
            line = _replaceMediaURL(line, res['ha_source'])
        line = _replaceXML(line, "hostname", vm_name)
        f.write(line)
    f.close()

    extra_args = "YAST_SKIP_XML_VALIDATION=1"
    autoyast = "%s/%s" % (dummy_folder,vm_name)
    parent_fd, child_fd = multiprocessing.Pipe()
    process = multiprocessing.Process(target=installVM,
                            args=(vm_name, disk, vm["ostype"],
                                  vm["vcpus"], vm["memory"],
                                  vm["disk_size"], res["sle_source"],
                                  vm["nic"], vm["second_nic"], vm["graphics"],
                                  extra_args, autoyast, child_fd),
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
    print("Note: Using virt-install: %s." % VIRT_INSTALL)
    for i in range(len(vm_list)):
        vm = vm_list[i]
        vm_name = vm['name']

        vm, disk = parse_vm_args(vm, devices)
        if base_image != "" :
            disk = "qcow2:" + base_image

        print "Note: Prepare to install virt-machine %s in disk(base:%s) %s." % ( vm['name'], base_image, disk )

        vm_list[i] = vm
        process = {}
        process["autoyast"], process["pipe"], process['process'] = run_install_cmd(os_settings, vm_name, vm, disk, res)
        processes[vm_name] = process
        process["process"].start()
        time.sleep(10)

    for vm in vm_list:
        vm_name = vm['name']
        processes[vm_name]["process"].join(MAX_VM_INSTALL_TIMEOUT)
        if clean_up:
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
    print "\t        autoyast files in '../confs/autoyast/',"
    print "\t        will select automatically based on source."
    sys.exit(1)

if __name__ == "__main__":
    #getSUSEVersionViaURL("http://mirror.suse.asia/dist/install/SLP/SLES-11-SP4-GM/x86_64/DVD1/")
    #getSUSEVersionViaURL("http://mirror.suse.asia/dist/install/SLP/SLE-12-SP3-Server-GM/x86_64/DVD1/")
    #getSUSEVersionViaURL("http://mirror.suse.asia/dist/install/SLP/SLE-15-Installer-LATEST/x86_64/DVD1/")
    #getSUSEVersionViaURL("http://mirror.suse.asia/dist/install/SLP/SLE-16-Installer-LATEST/x86_64/DVD1/")
    #getSUSEVersionViaURL("http://mirror.suse.asia/dist/install/SLP/SLE-15-SP2-Full-Beta1/x86_64/DVD1")
    #getSUSEVersionViaURL("http://mirror.suse.asia/dist/install/SLP/openSUSE-Leap-15.1/x86_64/DVD1/")
    #getSUSEVersionViaURL("http://download.suse.de/install/SLP/openSUSE-Tumbleweed/x86_64/DVD1/")
    #find_autoyast_file("http://mirror.suse.asia/dist/install/SLP/SLE-15-SP2-Full-Beta4/x86_64/DVD1/")

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
