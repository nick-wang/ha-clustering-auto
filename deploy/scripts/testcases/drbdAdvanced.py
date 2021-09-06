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
ENABLE_FIO= config.get(section, 'FIO_TEST')


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

    sleep(5)
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
        sleep(5)
        shell("ssh root@%s crm config delete res-%s" % (cluster_env["IP_NODE1"], RESNAME))

        run = shell("ssh root@%s crm configure show |grep %s" % (cluster_env["IP_NODE1"], RESNAME))

        if run.output():
            message = "Failed to delete DRBD resource %s." % RESNAME
            output = "\n".join(run.output())

    #Start the TEST resource with drbdadm
    sleep(5)
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

    #Need all role in secondary before test.
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
    package = "fio"
    for key in cluster_env.keys():
        if key.startswith("IP_NODE"):
            run = shell("ssh root@%s rpm -qi %s" % (cluster_env[key], package))

            if run.code != 0:
                #Try install package fio
                cmd = "zypper --non-interactive install --force-resolution %s" % package
                run = shell("ssh root@%s %s" % (cluster_env[key], cmd))

                if run.code != 0:
                    message = "Can't install '%s' package." % package
                    output = "\n".join(run.output())

    #Skipall following test cases when this failed
    if message != "" or output != "":
        result["skipall"] = True

    result["message"] = message
    result["output"] = output

    return result


def fioTests(args=None):
    message = ""
    output = ""
    result = {"status":"fail", "message":"", "output":"", "skipall": False}

    cluster_env = args[0]

    #Own test steps
    xmldir = args[2]

    info = libDRBD.getDRBDInfo(cluster_env)

    for i in info:
        if RESNAME == i["name"]:
            device = i["device"]

    if device:
        #Promote on the first node
        shell("ssh root@%s drbdadm primary %s" % (cluster_env["IP_NODE1"], RESNAME))

        sleep(1)
        run = shell("ssh root@%s drbdadm role %s" % (cluster_env["IP_NODE1"], RESNAME))

        if not run.output() and run.output()[0] != "Primary":
            message = "Can't promote DRBD res %s." % RESNAME
            output = "\n".join(run.output())
    else:
        message = "Fail to find DRBD device of res %s." % RESNAME
        output = RESNAME

    if message == "":
        # fio test
        run = shell("./testcases/scripts/drbdFioTest.py -n {} -d {} -o {}".format(
                    cluster_env["IP_NODE1"], device, xmldir))

        if run.code != 0:
            message = "Fail to run Fio test."
            output = "\n".join(run.output())

    if message == "":
        result["status"] = "pass"

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
                 ('drbdWriteMD5sum', 'DRBD.writeMD5', verifyMD5)]
                 #('ConfigureRes', 'SetupCluster.resources', runConfigureRes)]

    if ENABLE_FIO:
        cases_def.extend([('drbdFioRequirements', 'DRBD.Fio', fioRequirements),
                          ('drbdFioBasicTest', 'DRBD.Fio', fioTests)])

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
