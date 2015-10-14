#! /usr/bin/python

import os, sys, re
from junit_xml import TestSuite, TestCase

from library.libJunitXml import assertCase, skipCase
from library.libReadConf import readClusterConf

def get_result(args=None):
    message = ""
    output = ""
    result = {"status":"fail", "message":"", "output":"", "skipall": False}

    cluster_env = args[0]
    testcase = args[1]
    logfile = args[2]

    tmp = get_result_of_testcase(testcase, logfile)
    if tmp['calls'] > 0 and tmp['failure'] == 0:
        if tmp['skip'] == 0:
            result["status"] = "pass"
        else:
            result["status"] = "skip"
    elif tmp['calls'] > 0:
        message = "Running testcase %s failed." % testcase
        output = tmp["output"]

    return result

def get_result_of_testcase(testcase, logfile):
    result = {}

    f = open(logfile, 'r')

    result = {}
    failed = False
    result["output"] = ""
    for line in f.readlines():
        if testcase not in line:
            continue
        
        pattern=" *%s: *\{'auditfail': (\d), 'failure': (\d), 'skipped': (\d), 'calls': (\d)\}" % testcase
        tmp = re.search(pattern, line)
        if tmp is not None:
            result['auditfail'] = int(tmp.groups()[0])
            result['failure'] = int(tmp.groups()[1])
            result['skip'] = int(tmp.groups()[2])
            result['calls'] = int(tmp.groups()[3])
        if "FAILED" in line:
            result['output'] = line

    return result

def Run(conf, xmldir):
    logfile = "%s/my.log" % xmldir
    cluster_env = readClusterConf(conf)

    testcases = []
    #Name of Test Suite
    TestSuiteName = "Running pacemaker-cts"
    #Name of junit xml file
    JunitXML = "junit-pacemaker-cts-ha.xml"

    #Define testcases
    #testcases = [(TestcaseName, TestcaseClass, TestcaseFunction)]
    #eg.
    # ('PacemakerService', 'SetupCluster.service', runPackmakerService)
    #Define function runPackmakerService before using
    cases_def = [("Test Flip", "Pacemaker-cts", get_result),
                 ("Test Restart", "Pacemaker-cts", get_result),
                 ("Test Stonithd", "Pacemaker-cts", get_result),
                 ("Test StartOnebyOne", "Pacemaker-cts", get_result),
                 ("Test SimulStart", "Pacemaker-cts", get_result),
                 ("Test SimulStop", "Pacemaker-cts", get_result),
                 ("Test StopOnebyOne", "Pacemaker-cts", get_result),
                 ("Test RestartOnebyOne", "Pacemaker-cts", get_result),
                 ("Test PartialStart", "Pacemaker-cts", get_result),
                 ("Test Standby", "Pacemaker-cts", get_result),
                 ("Test MaintenanceMode", "Pacemaker-cts", get_result),
                 ("Test ResourceRecover", "Pacemaker-cts", get_result),
                 ("Test ComponentFail", "Pacemaker-cts", get_result),
                 ("Test Reattach", "Pacemaker-cts", get_result),
                 ("Test SpecialTest1", "Pacemaker-cts", get_result),
                 ("Test NearQuorumPoint", "Pacemaker-cts", get_result)]#,
#                 ("Test RemoteBasic", "Pacemaker-cts", get_result),
#                 ("Test RemoteStonithd", "Pacemaker-cts", get_result),
#                 ("Test RemoteMigrate", "Pacemaker-cts", get_result),
#                 ("Test RemoteRscFailure","Pacemaker-cts", get_result)]

    #Not necessary to modify the lines below!
    skip_flag = False
    for a_case in cases_def:
        case = TestCase(a_case[0], a_case[1])
        testcases.append(case)

        if skip_flag:
            skipCase(case, "Pacemaker service of the first node not started.")
            continue
        skip_flag = assertCase(case, a_case[2], cluster_env, a_case[0], logfile)

    ts = TestSuite(TestSuiteName, testcases)

    with open(xmldir+"/"+JunitXML, "w") as f:
        ts.to_file(f, [ts])

if __name__ == "__main__":
    Run(sys.argv[1], sys.argv[2])
