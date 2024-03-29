#!/usr/bin/python3

import sys, os, re

from junit_xml import TestSuite, TestCase

from library.libJunitXml import assertCase, skipCase
from library.libCommon import readClusterConf

def runPackmakerService(args=None):
    message = ""
    output = ""
    result = {"status":"fail", "message":"", "output":"", "skipall": False}

    cluster_env = args[0]

    #Own test steps
    lines = os.popen("ssh root@%s crm_mon -1r" % cluster_env["IP_NODE1"]).readlines()
    for line in lines:
        if re.match("Connection to cluster failed:", line) is not None:
            message = "Packmaker service not started."
            output = line
            break
    else:
        result["status"] = "pass"

    result["message"] = message
    result["output"] = output

    #Skipall following test cases when this failed
    if result["status"] == "fail":
        result["skipall"] = True

    return result

def runNodesNumber(args=None):
    message = ""
    output = ""
    result = {"status":"fail", "message":"", "output":"", "skipall": False}

    cluster_env = args[0]

    #Own test steps
    lines = os.popen("ssh root@%s crm_mon -1r" % cluster_env["IP_NODE1"]).readlines()
    for line in lines:
        tmp = re.match("(\d+) nodes? and (\d+) resources? configured", line)
        if tmp is not None:
            if int(tmp.groups()[0]) == int(cluster_env["NODES"]):
                result["status"] = "pass"
            else:
                message = "Not all nodes configured."
                output = "Only %s of %s nodes configured." % (tmp.groups()[0], cluster_env["NODES"])
            break

        #In sle15, format is changed, eg
        #  * 2 nodes configured
        tmp = re.match(" * \* (\d+) nodes? configured", line)
        if tmp is not None:
            if int(tmp.groups()[0]) == int(cluster_env["NODES"]):
                result["status"] = "pass"
            else:
                message = "Not only one resources configured."
                output = "%s custom resources configured." % tmp.groups()[0]
            break

    result["message"] = message
    result["output"] = output

    return result

def runNodesStatus(args=None):
    message = ""
    output = ""
    result = {"status":"fail", "message":"", "output":"", "skipall": False}

    cluster_env = args[0]

    #Own test steps
    lines = os.popen("ssh root@%s crm_mon -1r" % cluster_env["IP_NODE1"]).readlines()
    for line in lines:
        if re.search("OFFLINE:", line) is not None:
            message = "Not all nodes started."
            output = line
            break
    else:
        result["status"] = "pass"

    result["message"] = message
    result["output"] = output
    return result

def runConfigureRes(args=None):
    message = ""
    output = ""
    result = {"status":"fail", "message":"", "output":"", "skipall": False}

    cluster_env = args[0]

    lines = os.popen("ssh root@%s crm_mon -1r" % cluster_env["IP_NODE1"]).readlines()
    for line in lines:
        tmp = re.match("(\d+) nodes? and (\d+) resources? configured", line)
        if tmp is not None:
            #Only one resource - sbd
            if int(tmp.groups()[1]) == 1:
                result["status"] = "pass"
            else:
                message = "Not only one resources configured."
                output = "%s custom resources configured." % tmp.groups()[1]
            break

        #In sle15, format is changed, eg
        # * 1 resource instance configured
        tmp = re.match(" * \* (\d+) resources? instance configured", line)
        if tmp is not None:
            #Only one resource - sbd
            if int(tmp.groups()[0]) == 1:
                result["status"] = "pass"
            else:
                message = "Not only one resources configured."
                output = "%s custom resources configured." % tmp.groups()[0]
            break

    result["message"] = message
    result["output"] = output
    return result

def activeStonith(args=None):
    message = ""
    output = ""
    result = {"status":"fail", "message":"", "output":"", "skipall": False}

    cluster_env = args[0]

    lines = os.popen("ssh root@%s crm_mon -1r" % cluster_env["IP_NODE1"]).readlines()
    for line in lines:
        tmp = re.match(".*_stonith\s*\(stonith:external/(.*)\):\s*.*", line)
        if tmp is not None:
            #Stonith resource configured, type tmp.groups()[0]
            result["status"] = "pass"
            break
    else:
        message = "No active stonithd resources configured."
        output = "No active stonithd resources configured."

    result["message"] = message
    result["output"] = output
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
                 ('ConfigureRes', 'SetupCluster.resources', runConfigureRes),
                 ('ConfigureRes', 'SetupCluster.resources', activeStonith)]

    #Not necessary to modify the lines below!
    skip_flag = False
    for a_case in cases_def:
        case = TestCase(a_case[0], a_case[1])
        testcases.append(case)
        if skip_flag:
            skipCase(case, "Can not test!",
                     "Pacemaker service of the first node not started.")
            continue
        skip_flag = assertCase(case, a_case[2], cluster_env)

    ts = TestSuite(TestSuiteName, testcases)

    with open(xmldir+"/"+JunitXML, "w") as f:
        ts.to_file(f, [ts])

    lines = os.popen("ssh root@%s crm_mon -1r" % cluster_env["IP_NODE1"]).readlines()
    with open(xmldir+"/"+"crm_mon", "w") as p:
        p.writelines(lines)

    lines = os.popen("ssh root@%s crm configure show" % cluster_env["IP_NODE1"]).readlines()
    with open(xmldir+"/"+"crm-configure", "w") as p:
        p.writelines(lines)

    lines = os.popen("ssh root@%s cat /etc/YaST2/*build*" % cluster_env["IP_NODE1"]).readlines()
    with open(xmldir+"/"+"host-build", "w") as p:
        p.writelines(lines)

    lines = os.popen("ssh root@%s journalctl" % cluster_env["IP_NODE1"]).readlines()
    with open(xmldir+"/"+"journalctl-log", "w") as p:
        p.writelines(lines)

    lines = os.popen("ssh root@%s cat /var/log/pacemaker/pacemaker.log" % cluster_env["IP_NODE1"]).readlines()
    with open(xmldir+"/"+"pacemaker.log", "w") as p:
        p.writelines(lines)

if __name__ == "__main__":
    Run(sys.argv[1], sys.argv[2])
