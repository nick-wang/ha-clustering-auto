#!/usr/bin/python

import sys, os, re

from junit_xml import TestSuite, TestCase

from library.libJunitXml import assertCase, skipCase
from library.libReadConf import readClusterConf

def runPackmakerService(cluster_env=None):
    isOK = False
    output = ""
    result = {"pass":False, "message":"", "output":"", "skipall": False}

    #Own test steps
    lines = os.popen("ssh root@%s crm_mon -1r" % cluster_env["IP_NODE1"]).readlines()
    for line in lines:
        if re.match("Connection to cluster failed:", line) is not None:
            output = line
            break
    else:
        isOK = True

    if isOK:
        result["pass"] = True
        return result
    else:
        result["message"] = "Packmaker service not started."
        result["output"] = output
        result["skipall"] = True
        return result

def runNodesNumber(cluster_env=None):
    isOK = False
    output = ""
    result = {"pass":False, "message":"", "output":"", "skipall": False}

    #Own test steps
    lines = os.popen("ssh root@%s crm_mon -1r" % cluster_env["IP_NODE1"]).readlines()
    for line in lines:
        tmp = re.match("(\d+) nodes and 0 resources configured", line)
        if tmp is not None:
            if int(tmp.groups()[0]) == int(cluster_env["NODES"]):
                isOK = True
            else:
                output = tmp.groups()[0]
            break

    if isOK:
        result["pass"] = True
        return result
    else:
        result["message"] = "Not all nodes configured."
        result["output"] = "Only %s of %s nodes configured." % (output, cluster_env["NODES"])
        return result

def runNodesStatus(cluster_env=None):
    isOK = False
    output = ""
    result = {"pass":False, "message":"", "output":"", "skipall": False}

    #Own test steps
    lines = os.popen("ssh root@%s crm_mon -1r" % cluster_env["IP_NODE1"]).readlines()
    for line in lines:
        if re.match("OFFLINE:", line) is not None:
            output = line
            break
    else:
        isOK = True

    if isOK:
        result["pass"] = True
        return result
    else:
        result["message"] = "Not all nodes started."
        result["output"] = output
        return result

def runConfigureRes(cluster_env=None):
    isOK = False
    output = ""
    result = {"pass":False, "message":"", "output":"", "skipall": False}

    lines = os.popen("ssh root@%s crm_mon -1r" % cluster_env["IP_NODE1"]).readlines()
    for line in lines:
        tmp = re.match("(\d+) nodes and (\d+) resources configured", line)
        if tmp is not None:
            if int(tmp.groups()[1]) == 0:
                isOK = True
            else:
                output = tmp.groups()[1]
            break

    if isOK:
        result["pass"] = True
        return result
    else:
        result["message"] = "Resources configured?"
        result["output"] = "%s custom resources configured." % output
        return result

def Run(conf, xmldir):
    cluster_env = readClusterConf(conf)

    testcases = []
    #Name of Test Suite
    TestSuiteName = "Setup HA Cluster"
    #Name of junit xml file
    JunitXML = "junit-setup-ha.xml"

    #Define testcases
    #testcases = [(TestcaseName, TestcaseClass, TestcaseFunction)]
    #eg.
    # ('PacemakerService', 'SetupCluster.service', runPackmakerService)
    #Define function runPackmakerService before using
    cases_def = [('PacemakerService', 'SetupCluster.service', runPackmakerService),
                 ('NodesNumber', 'SetupCluster.nodes', runNodesNumber),
                 ('NodesStatus', 'SetupCluster.nodes', runNodesStatus),
                 ('ConfigureRes', 'SetupCluster.resources', runConfigureRes)]

    #Not necessary to modify the lines below!
    skip_flag = False
    for a_case in cases_def:
        case = TestCase(a_case[0], a_case[1])
        if skip_flag:
            skipCase(case, "Pacemaker service of the first node not started.")
        skip_flag = assertCase(case, a_case[2], cluster_env)

        testcases.append(case)

    ts = TestSuite(TestSuiteName, testcases)

    with open(xmldir+"/"+JunitXML, "w") as f:
        ts.to_file(f, [ts])

if __name__ == "__main__":
    Run(sys.argv[1], sys.argv[2])
