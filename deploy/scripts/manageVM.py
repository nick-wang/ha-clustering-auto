#! /usr/bin/python

import os
import sys
import yaml
import libvirt

class managerVM:
    def __init__(self, vmname, path):
        self.vmname = vmname
        self.path = path
        self.dom = getDomain()

#************the life cycle***********************
    def destroy_vm(self):
        if self.dom is None:
            return -1
        self.dom.destroy()
        return 0
    
    def undefine_vm(self):
        if self.dom is None:
            return -1
        self.dom.undefine()
        return 0
    
    def removefiles(self):
        path = self.path
        if os.path.exists(path) == False:
            return -1
        for file1 in os.listdir(path):
             os.remove("%s/%s" % (path, file1)) 
        return 0
    
    def reboot_vm(self, force=False):
        if self.dom is None:
            return -1
        if force:
            self.dom.reset(1)
        else:
            self.dom.reboot(1)
        return 0
    
    def start_vm(self):
        if self.dom is None:
            return -1
        self.dom.start()
        return 0

    def shutdown(self)
        if self.dom is None:
            return -1
        self.dom.shutdown()

    def migrate(self):
        pass

    def save(self, to):
        if self.dom is None:
            return -1
        self.dom.save(path)
        return 0

    def resume(self):
        if self.dom is None:
            return -1
        self.dom.resume()
        return 0

    def suspend(self):
        if self.dom is None:
            return -1
        self.dom.suspend()
        return 0

#************the life cycle***********************

#************the configuration********************
    def setMaxMemory(self, memory)
        if self.dom is None:
            return -1
        self.dom.setMaxMemory(memory)
        return 0

    def setMemory(self, memory):
        if self.dom is None:
            return -1
        self.dom.setMemory(memory)
        return 0

    def setVcpus(self, vcpus):
        if self.dom is None:        
            return -1
        self.dom.setVcpus(vcpus)
        return 0

    def attachDevice(self, xml):
        if self.dom is None:
            return -1
        self.dom.attachDevice(xml)
        return 0

    def detachDevice(self, xml):
        if self.dom is None:
            return -1
        self.dom.detachDevice(xml)
        return 0

#************the configuration********************

#************the utils library********************
    def getDomain(self,vmname):
        conn = libvirt.open("qemu:///system")
        dom = conn.lookupByName(vmname)
        if dom is None:
            print '%s does not exist' %vmname 
            return None
        return dom
#************the utils library********************
#end of class managerVM
