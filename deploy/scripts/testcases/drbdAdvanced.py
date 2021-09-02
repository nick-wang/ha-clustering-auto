#!/usr/bin/python3

import sys, os, re
import configparser
import library.libDRBD as libDRBD

from time import sleep
from junit_xml import TestSuite, TestCase

from library.libJunitXml import assertCase, skipCase
from library.libReadConf import readClusterConf
from library.shell import shell

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

            run = shell("ssh root@%s %s" % (cluster_env["IP_NODE1"], cmd))

            # TEST resource should >= 2G
            if run.output() and int(run.output()[0]) >= 2147483648:
                break

    else:
        skipall = True
        message = "Size of DRBD %s backing device smaller than 2G." % RESNAME
        output = str(line)

    #Skipall following test cases when this failed
    result["skipall"] = skipall

    if not skipall:
        result["status"] = "pass"

    result["message"] = message
    result["output"] = output

    return result


def removeTestRes(args=None):
    '''
    Remove DRBD test resource from pacemaker.
    '''
    message = ""
    output = ""
    result = {"status":"fail", "message":"", "output":"", "skipall": False}

    cluster_env = args[0]

    #Own test steps
    #Demote the TEST resource
    shell("ssh root@%s crm resource stop ms_%s" % (cluster_env["IP_NODE1"], RESNAME))

    sleep(3)
    run = shell("ssh root@%s crm resource status ms_%s" % (cluster_env["IP_NODE1"],
                                                                RESNAME))
    if run.errors():
        for l in run.errors():
            #Resource stopped or not configured at all
            if "NOT running" or "No such device or address" in l:
                break
        else:
            message = "Failed to stop DRBD resource %s." % RESNAME
            output = l
    else:
        message = "Still have running DRBD resource %s in crm." % RESNAME
        output = l

    if message == "":
        #DRBD resource will stop after deleted
        shell("ssh root@%s crm config delete ms_%s" % (cluster_env["IP_NODE1"], RESNAME))
        shell("ssh root@%s crm config delete res-%s" % (cluster_env["IP_NODE1"], RESNAME))

        run = shell("ssh root@%s crm configure show |grep %s" % (cluster_env["IP_NODE1"], RESNAME))

        if run.output():
            message = "Failed to delete DRBD resource %s." % RESNAME
            output = "\n".join(run.output())

    #Start the TEST resource with drbdadm
    sleep(3)
    for key in cluster_env.keys():
        if key.startswith("IP_NODE"):
            shell("ssh root@%s drbdadm up %s" % (cluster_env[key], RESNAME))

            sleep(2)
            run = shell("ssh root@%s drbdadm status %s" % (cluster_env[key], RESNAME))

            if run.errors():
                message = "Failed to start DRBD resource %s." % RESNAME
                output = "\n".join(run.errors())

    #Skipall following test cases when this failed
    if message != "" or output != "":
        result["skipall"] = True

    if not result["skipall"]:
        result["status"] = "pass"

    result["message"] = message
    result["output"] = output

    return result


def verifyMD5(args=None):
    message = ""
    output = ""
    result = {"status":"fail", "message":"", "output":"", "skipall": False}

    cluster_env = args[0]

    #Own test steps
    cluster_conf = args[1]
    xmldir = args[2]
    loop = 2

    cmd = "./testcases/scripts/drbdMD5sum.sh %s %s %s %s" % (RESNAME, loop,
            xmldir, cluster_conf)

    #Write/verify the md5sum
    shell(cmd)

    fd = open(xmldir + "/drbdMD5sum-result", "r")
    lines = [x.strip() for x in fd.readlines()]
    fd.close()

    for line in lines:
        if not line.startswith("myrandom.file"):
            continue

        if "OK" not in line:
            message = "Verify MD5sum failed!"
            output = line

    if message == "":
        result["status"] = "pass"

    result["message"] = message
    result["output"] = output

    return result


def fioRequirements(args=None):
    message = ""
    output = ""
    result = {"status":"fail", "message":"", "output":"", "skipall": False}

    cluster_env = args[0]

    #Own test steps
    for key in cluster_env.keys():
        if key.startswith("IP_NODE"):
            shell("ssh root@%s rpm -qi fio" % cluster_env[key])

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
    cases_def = [('drbdAdvancedRequirements', 'TEST.requirements', preRequirements),
                 ('drbdAdvancedRemoveRes', 'TEST.RemoveRes', removeTestRes),
                 ('drbdWriteMD5sum', 'DRBD.writeMD5', verifyMD5),
                 ('drbdFioRequirements', 'DRBD.Fio', fioRequirements)]
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
        print("Running test case %s:%s()..." % (__file__, a_case[0]))
        skip_flag = assertCase(case, a_case[2], cluster_env, conf, xmldir)
        sleep(3)

    ts = TestSuite(TestSuiteName, testcases)

    with open(xmldir+"/"+JunitXML, "w") as f:
        ts.to_file(f, [ts])

if __name__ == "__main__":
    Run(sys.argv[1], sys.argv[2])
