#! /usr/bin/python

import yaml
import os, sys

# yaml file example
'''
resources:
  sle_source: http://147.2.207.237/repo/UNTESTED/SLE-12-SP1-Server-DVD-x86_64/
  ha_source: http://147.2.207.237/repo/UNTESTED/SLE-12-SP1-HA-DVD-x86_64/

nodes:
- name: node01
  mac: 00:0C:29:6B:CA:02
  disk: qcow2:/mnt/vm/sles_liub/sles12sp1-HA-liubin_node01.qcow2
  ostype: sles11
  vcpus: 2
  memory: 1024
  disk_size: 8192
  nic:
  graphics:
  os_settings:

- name: node02
  mac: 00:0C:29:C9:21:D5
  disk: qcow2:/mnt/vm/sles_liub/sles12sp1-HA-liubin_node02.qcow2
  ostype: sles11
  vcpus: 2
  memory: 1024
  disk_size: 8192
  nic:
  graphics:
  os_settings:  

- name: node03
  mac: 00:0C:29:D7:4C:31
  disk: qcow2:/mnt/vm/sles_liub/sles12sp1-HA-liubin_node03.qcow2
  ostype: sles11
  vcpus: 2
  memory: 1024
  disk_size: 8192
  nic:
  graphics:
  os_settings:

iscsi:
  target_ip: 147.2.207.237
  target_lun: iqn.2015-08.suse.bej.bliu:441a202b-6aa3-479f-b56f-374e2f38ba20
'''

class GET_VM_CONF:
    def __init__(self, url):
        self.ya = self.get_yaml(url)
        self.structs = {'iscsi': ('target_ip', 'target_lun'),
                        'resources': ('sle_source', 'ha_source')}

    def get_yaml(self, url):
        '''
            Get group infomation from client.yaml
        '''
        with open(url,'r') as f:
            ya = yaml.load(f)
        return ya

    def get_single_section_conf(self, section):
        ''' 
            Only for single section, can not use for list. 
        '''
        if not self.structs.has_key(section):
            print "Need to config a new section (%s)." % section
            sys.exit(4)

        conf = {}
        struct = self.ya.get(section)

        if struct is None:
            print "Lack of '%s' section in yaml file." % section
            return

        # So far, only for 'iscsi' and 'resources'
        for ele in self.structs[section]:
            conf[ele] = struct.get(ele)

        return conf

    def get_vms_conf(self):
        vms = {}
        nodes = self.ya.get('nodes')
        vm_elements = ('name', 'mac', 'ostype', 'disk', 'vcpus', 'memory',
                       'disk_size', 'nic', 'graphics', 'os_settings' )

        if nodes is None:
            print "Lack of 'nodes' section in yaml file."
            return

        for node in nodes:
            if node.get('name') is None:
                print "Error! Node name can not empty."
                sys.exit(3)

            vm = {}
            for ele in vm_elements:
                vm[ele] = node.get(ele)

            if not vms.has_key(vm['name']):
                vms[vm['name']] = vm
            else:
                print "Error! Duplicate node name(%s) detected." % vm['name']
                sys.exit(2)
        return vms

def test():
    # vm_list.yaml is for testing only.
    # Should get the yaml configuration file from scheduler(jenkins).
    deployfile = "%s/%s" % (os.getcwd(), 'templete/vm_list.yaml')

    dp = GET_VM_CONF(deployfile)
    vm_list = dp.get_vms_conf()

    for i in dp.structs.keys():
        print dp.get_single_section_conf(i)

    print vm_list


if __name__ == "__main__":
    '''
        This is a library to parse yaml file, should not running via itself.
    '''
    test()