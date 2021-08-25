#!/usr/bin/python3

import sys, os, re
import configparser
import library.libDRBD as libDRBD

from time import sleep
from junit_xml import TestSuite, TestCase

from library.libJunitXml import assertCase, skipCase
from library.libReadConf import readClusterConf

config = configparser.ConfigParser({'TEST_RESOURCE':'dummy'})
config.read('testcases/config.ini')
section = 'DRBD'

# TEST resource
RESNAME = config.get(section, 'TEST_RESOURCE')

def preRequirements(args=None):
    message = ""
    output = ""
    result = {"status":"fail", "message":"", "output":"", "skipall": False}

    cluster_env = args[0]

    #Own test steps
    skipall = False

    line = 0
    info = libDRBD.getDRBDInfo(cluster_env)

    #1. Should have TEST resource configured
    for i in info:
        if RESNAME == i["name"]:
            cmd = "lsblk -b %s |grep -v NAME| xargs |cut -d ' ' -f 4" % i["device"]
            line = os.popen("ssh root@%s %s" %
                (cluster_env["IP_NODE1"], cmd)).readline().strip()

            # TEST resource should >= 2G
            if line is not None and int(line) >= 2147483648:
                break
    else:
        skipall = True
        message = "No 2G TEST resource configured."
        output = str(line)

    #Skipall following test cases when this failed
    result["skipall"] = skipall
    result["message"] = message
    result["output"] = output

    return result


def Run(conf, xmldir):
    cluster_env = readClusterConf(conf)

    testcases = []
    #Name of Test Suite
    TestSuiteName = "DRBD advanced testing"
    #Name of junit xml file
    JunitXML = "junit-drbd-advanced.xml"

    #Define testcases
    #testcases = [(TestcaseName, TestcaseClass, TestcaseFunction)]
    #eg.
    # ('PacemakerService', 'SetupCluster.service', runPackmakerService)
    #Define function runPackmakerService before using
    cases_def = [('drbdAdvancedRequirements', 'TEST.requirements', preRequirements)]
                 #('ConfigureRes', 'SetupCluster.resources', runConfigureRes)]

    #Not necessary to modify the lines below!
    skip_flag = False
    for a_case in cases_def:
        case = TestCase(a_case[0], a_case[1])
        testcases.append(case)
        if skip_flag:
            skipCase(case, "Can not test!",
                     "Requirement of DRBD advanceding test not ready.")
            continue
        skip_flag = assertCase(case, a_case[2], cluster_env)
        sleep(3)

    ts = TestSuite(TestSuiteName, testcases)

    with open(xmldir+"/"+JunitXML, "w") as f:
        ts.to_file(f, [ts])

if __name__ == "__main__":
    Run(sys.argv[1], sys.argv[2])
