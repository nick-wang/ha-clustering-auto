#!/usr/bin/python

import sys, os
import re, shutil
import subprocess
import yaml
import getopt

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
            # "resync-never-connected.KNOWN": timeout or hang sometimes
            #{"name":"resync-never-connected.KNOWN", "nodes":0},
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

s_dir = "/drbdtest/drbd-test-*"

error_logs = ["Traceback", "Timeout waiting"]
retry_logs = error_logs
need_retry = True

nodelist = []

def usage():
    print("usage:")
    print("\t./LinbitTest.py -f <configuration> -c <case> -r")
    sys.exit(1)

def get_option():
    options = {"configuration": "/tmp/cluster-configuration/cluster_conf", "case": None,
               "resume": False}

    try:
        opts, args = getopt.getopt(sys.argv[1:], "f:c:r",
                    ["configuration=", "case=", "resume"])
    except getopt.GetoptError:
        print("Get options Error!")
        sys.exit(2)

    for opt, value in opts:
        if opt in ("-f", "--configuration"):
            options["configuration"] = value
        elif opt in ("-c", "--case"):
            options["case"] = value
        elif opt in ("-r", "--resume"):
            options["resume"] = True
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
        print("Resource existed!!!")
        print("Get the resource name: %s" % res)
    else:
        #print( "No resource defined.")
        return 0

    if show == True:
        os.system("drbdsetup status %s --verbose --statistics" % res[0])

    return 1

def log_collection(srcdir=s_dir, output_dir="/drbdtest/log"):
    logs=("Linbit-drbd-test.yml", "log", "output.log")

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    src=find_dir(srcdir)+os.path.sep
    dst=output_dir+os.path.sep

    for log in logs:
        if os.path.isdir(src+log):
            shutil.copytree(src+log, dst+log)
        else:
            shutil.copyfile(src+log, dst+log)

def generate_yaml_result(testsuite, output='Linbit-drbd-test.yml'):
    # Using "testsuite" as data directly, will output like:
    # - !!python/object:__main__.Testcase
    #   error: false
    #   isdirty: false
    #   message: null
    #   name: resync-never-connected.KNOWN
    #   need_clean: true
    #   nodes: 0
    #   output: null
    #   result: PASSED
    #   srcdir: /drbdtest/drbd-test-*
    data = {}
    for test in testsuite:
        tmp_test = {"error": test.error,
                    "isdirty": test.isdirty,
                    "message": test.message,
                    "nodes": test.nodes,
                    # No need to include output, all in output.log/*
                    # "output": test.output,
                    "result": test.result,
                   }

        data[test.name] = tmp_test

    # All test should have same srcdir
    yaml_dir = find_dir(test.srcdir)

    with open(yaml_dir+os.path.sep+output, 'w') as fd:
        yaml.dump(data, fd, default_flow_style=False)

class Testcase(object):
    ''' Tstcase to run Linbit drbd-test '''

    number = 0

    def __init__(self, name=None, nodes=0,
                 srcdir=s_dir, need_clean=True):
        self.name = name
        self.nodes = nodes
        self.need_clean = need_clean
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
        # Sometimes fail due to network issue
        self.times = 1
        self.old_output = None
        self.need_do = True

        self.__class__.number += 1;

    def __str__(self):
        return ("%s: Test result is %s." %
            (self.name, self.result))

    def run(self):
        print("** Start to run case \"%s\" (%d):" % (self.name, self.times))
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
        self.output = [ line.decode("utf-8").strip() for line in worker.stdout.readlines() ]
        worker.wait()

        self.check_result()

        # Cleanup the env after every run
        if self.need_clean:
            self.cleanup()

    def record_output(self):
        os.chdir(find_dir(self.srcdir))
        if not os.path.exists("output.log"):
            os.mkdir("output.log")
        with open("output.log/%s" % self.name, "w") as fd:
            fd.writelines(self.output)
        if self.old_output != None:
            with open("output.log/old-%s" % self.name, "w") as fd:
                fd.writelines(self.old_output)

    def check_result(self):
        self.record_output()

        self.result = "FAILED"
        for line in self.output:
            for e_pa in error_logs:
                if re.search(e_pa, line):
                    # Sometimes network cause timeout, retry in this case
                    if need_retry and e_pa in retry_logs and self.times <= 3:
                        print("   %s, case retry..." % e_pa)
                        self.need_do = True
                        self.old_output = self.output
                        self.times += 1
                        return

                    print(" Found '%s', case '%s' FAILED!" % (e_pa, self.name))
                    self.message = "Found '%s' in '%s', case FAILED!"  % \
                        (e_pa,line)
                    self.error = True
                    self.need_do = False
                    return
        else:
            self.result = "PASSED"
            self.need_do = False
            return

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

    if options["resume"]:
        # Need to cleanup on each node
        for node in nodelist:
            os.system('ssh root@%s \
                "/tmp/cluster-configuration/scripts/drbd/libs/cleanLinbitTest.py"' %
                node)
        return 0

    testsuite = []
    for case in TESTCASES:
        if options["case"] is None or options["case"] == case["name"]:
            aTest = Testcase(**case)
            testsuite.append(aTest)
            while aTest.need_do:
                aTest.run()

    generate_yaml_result(testsuite)

    log_collection()

if __name__ == "__main__":
    main()
