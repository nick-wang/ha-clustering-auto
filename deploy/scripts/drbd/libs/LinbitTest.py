#!/usr/bin/env python2

import sys, getopt, os
import re
import subprocess

from glob import glob
from pprint import pprint

TESTCASES = ({"name":"connect", "nodes": 0},
            {"name":"initial-resync", "nodes":0},
            {"name":"latency", "nodes":2},
            {"name":"misaligned-bio", "nodes":2},
            {"name":"switch-primaries", "nodes":2},
            {"name":"ref-count", "nodes":2},
            {"name":"add-connect-delete", "nodes":2},
            {"name":"add-path-multiple-times", "nodes":2},
            {"name":"ahead-behind.KNOWN", "nodes":2},
            {"name":"resize.KNOWN", "nodes":2},
            {"name":"resync-never-connected.KNOWN", "nodes":0},
            # "diskless": can't finish resource.skip_initial_sync()
            #            because one of them is diskless...
            #{"name":"diskless", "nodes":0},
            #
            # "attach-detach.KNOWN": Attach/detach will hang... 
            #{"name":"attach-detach.KNOWN", "nodes":0},
            #
            # "multi-path": Need the other path "eth0:1"
            #{"name":"multi-path", "nodes":2},
            #
            # "compat-with-84": No /data/drbd-8.4/drbd/drbd.ko
            #{"name":"compat-with-84", "nodes":2},
            #
            # "multiple-devices.KNOWN": enable an already enabled connection
            # Should add disks in the same time and connect only once
            #{"name":"multiple-devices.KNOWN", "nodes":2},
            #
            # "tl_restart-stress.KNOWN": enable an already enabled connection
            # Should add disks in the same time and connect only once
            #{"name":"tl_restart-stress.KNOWN", "nodes":2},
            ) 

error_logs = ["Traceback", "Timeout waiting"]
s_dir = "/drbdtest/drbd-test-*"

nodelist = []

def usage():
    print("usage:")
    print("\t./LinbitTest.py -f <configuration> -c <case>")
    sys.exit(1)

def get_option():
    options = {"configuration": "/tmp/cluster-configuration/cluster_conf", "case": None}

    try:
        opts, args = getopt.getopt(sys.argv[1:], "f:c:",
                    ["configuration=", "case="])
    except getopt.GetoptError:
        print("Get options Error!")
        sys.exit(2)

    for opt, value in opts:
        if opt in ("-f", "--configuration"):
            options["configuration"] = value
        elif opt in ("-c", "--case"):
            options["case"] = value
        else:
            usage()

    return options

def get_node_list_from_conf(conf="/tmp/cluster-configuration/cluster_conf"):
    fd = open(conf,"r") 
    lines = [ line.strip() for line in fd.readlines() ]
    fd.close()

    nodes = []
    pattern = re.compile("HOSTNAME_NODE[0-9]*=(.*)")
    for line in lines:
        tmp = re.match(pattern, line)
        if tmp is not None:
            nodes.append(tmp.groups()[0])
 
    return nodes

def find_dir(path):
    dirs = glob(path)
    if len(dirs) != 0:
        for d in dirs:
            if os.path.isdir(d):
                return d
        else:
            return "/tmp"
    else:
        return "/tmp"

def working_node_list(num):
    if num <= 0 or num > len(nodelist):
        return nodelist
    else:
        return nodelist[0:num]

def check_res_exist(show=False):
    res = [ line.strip() for line in
        os.popen("drbdsetup status |grep \"^\w\" |cut -d ' ' -f 1").readlines() ]
    if len(res) != 0 and show == True:
        print "Resource existed!!!"
        print "Get the resource name: %s" % res
    else:
        #print "No resource defined."
        return 0

    if show == True:
        os.system("drbdsetup status %s --verbose --statistics" % res[0])

    return 1

def log_collection():
    pass

def generate_junit_report():
    pass
    
class Testcase(object):
    ''' Tstcase to run Linbit drbd-test '''

    number = 0

    def __init__(self, name=None, nodes=0, 
                 srcdir=s_dir, need_clean=True, 
                 record=True):
        self.name = name
        self.nodes = nodes
        self.need_clean = need_clean
        self.record = record
        self.srcdir = srcdir

        # Is Env clean before running test case?
        self.isdirty = False
        # True when fail
        self.error = False
        # Output of test case
        self.output = None
        # Test result
        self.result = None
        # Error msg if failed
        self.message = None

        self.__class__.number += 1;

    def __str__(self):
        return ("%s: Test result is %s." % 
            (self.name, self.result))

    def run(self):
        print "** Start to run case \"%s\":" % self.name
        sys.stdout.flush()

        if self.need_clean:
            dirty = check_res_exist(show=False)
            if dirty != 0:
                self.isdirty = True

        os.chdir(find_dir(self.srcdir))

        arg = ["./tests/%s" % self.name]
        arg.extend(working_node_list(self.nodes))
 
        # call/check_output euqal Popen+wait
        worker = subprocess.Popen(args=arg, 
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.output = worker.stdout.readlines()
        worker.wait()

        self.check_result()

        # Cleanup the env after every run
        if self.need_clean:
            self.cleanup()

    def record_output(self):
        os.chdir(find_dir(self.srcdir))
        if not os.path.exists("output.log"):
            os.mkdir("output.log")
        fd = open("output.log/%s" % self.name, "w")
        fd.writelines(self.output)
        fd.close()

    def check_result(self):
        self.record_output()

        self.result = "FAILED"
        for line in self.output:
            for e_pa in error_logs:
                if re.search(e_pa, line):
                    print " Found '%s', case '%s' FAILED!" % (e_pa, self.name)
                    self.message = "Found '%s' in '%s', case FAILED!"  % \
                        (e_pa,line)
                    self.error = True
                    return
        else:
            self.result = "PASSED"

    def cleanup(self):
        # Need to cleanup on each node
        for node in nodelist:
            os.system('ssh root@%s \
                "/tmp/cluster-configuration/scripts/drbd/libs/cleanLinbitTest.py"' %
                node)

def main():
    options = get_option()

    # get nodes's list
    global nodelist
    nodelist = get_node_list_from_conf(options["configuration"])

    testsuite = []
    for case in TESTCASES:
        if options["case"] is None or options["case"] == case["name"]:
            aTest = Testcase(**case)
            testsuite.append(aTest)
            aTest.run()

    for test in testsuite:
        print test.name, test.result, test.isdirty

if __name__ == "__main__":
    main()
