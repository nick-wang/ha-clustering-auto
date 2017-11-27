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
  disk_size: 15360
  nic:
  graphics:
  os_settings:

- name: node02
  mac: 00:0C:29:C9:21:D5
  disk: qcow2:/mnt/vm/sles_liub/sles12sp1-HA-liubin_node02.qcow2
  ostype: sles11
  vcpus: 2
  memory: 1024
  disk_size: 15360
  nic:
  graphics:
  os_settings:

- name: node03
  mac: 00:0C:29:D7:4C:31
  disk: qcow2:/mnt/vm/sles_liub/sles12sp1-HA-liubin_node03.qcow2
  ostype: sles11
  vcpus: 2
  memory: 1024
  disk_size: 15360
  nic:
  graphics:
  os_settings:

repos:
- repo: http://download.suse.de/ibs/SUSE:/SLE-12:/Update/standard/
- repo: http://download.suse.de/ibs/SUSE:/SLE-12-SP1:/Update/standard/

devices:
  disk_dir: /mnt/vm/sles_ha_auto/
  nic: br0
  vcpus:
  memory:
  disk_size:
  backing_file: yes
  sharing_backing_file: yes

iscsi:
  target_ip: 147.2.207.237
  target_lun: iqn.2015-08.suse.bej.bliu:441a202b-6aa3-479f-b56f-374e2f38ba20
  shared_target_luns:
  - shared_target_lun:
    shared_target_ip:
  - shared_target_lun:
    shared_target_ip:
'''

class GET_VM_CONF:
    def __init__(self, url):
        self.ya = self.get_yaml(url)
        # 'lists' only support the list have one paramater
        # more than one paramater need to using other function
        # refer to 'nodes'
        self.lists = {'repos': 'repo'}
        self.structs = {'iscsi': ('target_ip', 'target_lun'),
                        'devices': ('disk_dir', 'nic', 'vcpus', 'memory', 'disk_size', 'backing_file', 'sharing_backing_file'),
                        'resources': ('sle_source', 'ha_source')}

    def is_key_none(self, key):
        if key is None:
            return True
        return False

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

        # So far, only for 'iscsi', 'devices' and 'resources'
        for ele in self.structs[section]:
            conf[ele] = struct.get(ele)

        return conf

    def get_list_section_conf(self, section):
        '''
            Only for list section with only one option.
            list section in yaml file starts with "-"
        '''
        if not self.lists.has_key(section):
            print "Need to config a new list section (%s)." % section
            sys.exit(4)

        structs = self.ya.get(section)

        if structs is None:
            print "Lack of '%s' section in yaml file." % section
            return []

        conf = []
        for struct in structs:
            # Error fix of AttributeError: 'str' object has no attribute 'get'
            # Because list option should starts with "-"
            if struct.get(self.lists[section]) is not None:
                conf.append(struct.get(self.lists[section]))

        return conf

    def get_vms_conf(self):
        vms = []
        if self.ya is None:
            return None
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

            if vm not in vms:
                vms.append(vm)
            else:
                print "Error! Duplicate node name(%s) detected." % vm['name']
                sys.exit(2)
        return vms

    def get_shared_target(self):
        targets = []
        if self.is_key_none(self.ya):
            return None
        iscsis = self.ya.get('iscsi')
        if self.is_key_none(iscsis):
            return None
        ip = iscsis.get('target_ip')
        target_luns = iscsis.get('shared_target_luns')
        if target_luns is None:
            return targets
        for iscsi in target_luns:
            tgt = iscsi.get('shared_target_lun')
            if tgt is None:
                continue
            target = {}
            target['shared_target_lun'] = tgt
            tgt_ip = iscsi.get('shared_target_ip')
            if tgt_ip is None:
                tgt_ip = ip
            target['shared_target_ip'] = tgt_ip

            if target not in targets:
                targets.append(target)

        return targets

def test(deployfile=""):
    # vm_list.yaml is for testing only.
    # Should get the yaml configuration file from scheduler(jenkins).
    if deployfile == '':
        deployfile = "%s/%s" % (os.getcwd(), '../confs/vm_list.yaml')

    dp = GET_VM_CONF(deployfile)
    vm_list = dp.get_vms_conf()
    target_list = dp.get_shared_target()

    for i in dp.structs.keys():
        print dp.get_single_section_conf(i)
    repos=dp.get_list_section_conf("repos")
    if len(repos) > 0:
        print " ".join(repos)
    print vm_list
    print target_list

if __name__ == "__main__":
    '''
        This is a library to parse yaml file, should not running via itself.
    '''
    if len(sys.argv) != 2:
        test()
    else:
        test(sys.argv[1])
