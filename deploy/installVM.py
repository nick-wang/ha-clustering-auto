import commands
import subprocess
import os
import sys
import multiprocessing
from getIPByName import get_ip_by_mac, GET_VM_CONF, write_cluster_conf

#SP_VERSION=SP1
#REL_VERSION=Beta2
#INSTANCE=ha004
#AUTOINS_TEMPLATE=/root/12SP1-Beta2-HA.autoinst.xml
#AUTOINS_TEMPLATE=sle12sp1-ha-autoinst.xml
#
#VMNAME=12${SP_VERSION}-${REL_VERSION}-${INSTANCE}
#VM_INSTALL_SOURCE=http://mirror.bej.suse.com/dist/install/\
#SLP/SLE-12-${SP_VERSION}-Server-${REL_VERSION}/x86_64/DVD1/
#
#AUTOINS_FILE=${VMNAME}.autoinst.xml
#cat ${AUTOINS_TEMPLATE} | \
#sed "s/\(HA-\).*\(\/x86_64\)/\1${REL_VERSION}\2/g" | \
#sed "s/<hostname.*/<hostname\>${VMNAME}<\/hostname\>/g" \
#> ${AUTOINS_FILE}
#
#echo << EOF | vm-install --debug \
#--os-type sles12 \
#--name "${VMNAME}" \
#--vcpus 1 \
#--memory 1024 \
#--disk qcow2:/work/images/${VMNAME}.qcow2,vda,disk,w,8192,sparse=0 \
#--source=${VM_INSTALL_SOURCE} \
#--nic bridge=br1,model=virtio \
#--graphics cirrus \
#--os-settings=${AUTOINS_FILE}





#EOF 
SP_VERSION=""
REL_VERSION=""
AUTOINS_TEMPLATE=""

def readConf(filePath):
    pass

#def installVM(VMName, disk, OSType="sles12", vcpus=1, memory=1024, disk_size=8192, source='http://mirror.bej.suse.com/dist/install/SLP/SLE-12-SP1-Server-LATEST/x86_64/DVD1/', nic='bridge=br1,model=virtio', graphics='cirrus', os_settings='sle12-ha-autoinst.xml'):
def installVM(VMName, disk, OSType, vcpus, memory, disk_size, source, nic, graphics, os_settings, child_fd):
    options = "--debug --os-type %s --name %s --vcpus %d --memory %d --disk %s,vda,disk,w,%d,sparse=0, --source %s --nic %s --graphics %s --os-settings=%s" \
              %(OSType, VMName, vcpus, memory, disk, disk_size, source, nic, graphics, os_settings)
    #cmd = "echo << EOF| vm-install %s%s%s" % (options, "\n\n\n\n\n\n\n", "EOF")
    
    print "cmd=%s" % cmd
    #status, output = commands.getstatusoutput(cmd)
    #p = subprocess.Popen(args=["vm-install", options], \
    #    stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    #p.communicate("\n\n\n\n\n\n\n")
    #print p.wait()
   
    os.system(cmd)

def installVMs(vm_list={}):
    processes = {}
    vms = vm_list.keys()
    print vms
    for vm in vm_list.keys():
        process = {}
        #init default values
        OSType="sles12"
        vcpus=1
        memory=1024
        disk_size=8192
        source='http://mirror.bej.suse.com/dist/install/SLP/SLE-12-SP1-Server-LATEST/x86_64/DVD1/'
        nic='bridge=br1,model=virtio'
        graphics='cirrus'
        os_settings='templete/my_ha_inst.xml'
        # get value from vm config
        disk = vm_list[vm]['disk']
        if vm_list[vm]['ostype'] is not None:
            ostype = vm_list[vm]['ostype']
        if vm_list[vm]['vcpus'] is not None:
            vcpus = vm_list[vm]['vcpus']
        if vm_list[vm]['memory'] is not None:
            memory= vm_list[vm]['memory']
        if vm_list[vm]['disk_size'] is not None:
            disk_size = vm_list[vm]['disk_size']
        if vm_list[vm]['source'] is not None:
            source = vm_list[vm]['source']
        if vm_list[vm]['nic'] is not None:
            nic = vm_list[vm]['nic']
        if vm_list[vm]['graphics'] is not None:
            graphics = vm_list[vm]['graphics']
        if vm_list[vm]['os_settings'] is not None:
            os_settings = vm_list[vm]['os_settings']

        f = open(os_settings, 'r')
        conf_str = f.read()
        f.close()
        f = open(vm, 'w')
        f.write(conf_str.replace("HOSTNAME", vm))
        f.close()

        os_settings = vm
        parent_fd, child_fd = multiprocessing.Pipe()
        process["process"] = multiprocessing.Process(target=installVM,
                                args=(vm, disk, ostype,vcpus, memory, disk_size, source, nic, graphics, os_settings, child_fd),
                                name=vm)
        process['pipe'] = parent_fd
        processes[vm] = process
        process["process"].start()

    for vm in vm_list.keys():
        processes[vm]["process"].join()

if __name__ == "__main__":
    newInstallation="false"
    vm_list={}
    deployfile = 'vm_list.yaml'
    dp = GET_VM_CONF(deployfile)
    vm_list = dp.get_vms_conf()
    if len(sys.argv) >= 2:
        newInstallation = sys.argv[2]
    if newInstallation.lower() == 'true':
        installVMs(vm_list)
