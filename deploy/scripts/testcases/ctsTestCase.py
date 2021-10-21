#!/usr/bin/python3

import os, sys, re
from junit_xml import TestSuite, TestCase

from library.libJunitXml import assertCase, skipCase
from library.libCommon import readClusterConf

def get_result(args=None):
    message = ""
    output = ""
    result = {"status":"fail", "message":"", "output":"", "skipall": False}

    cluster_env = args[0]
    testcase = args[1]
    logfile = args[2]

    tmp = get_result_of_testcase(testcase, logfile)

    if 'calls' not in list(tmp.keys()):
        return {"status":"skip", "message":"Testcase %s skipped" % testcase, "output":"skipped", "skipall": False}

    if tmp['calls'] > 0 and tmp['failure'] == 0:
        if tmp['skip'] == 0:
            result["status"] = "pass"
        else:
            result["status"] = "skip"
            result["message"] = "Testcase %s skipped" % testcase
    if tmp['calls'] == 0:
        result["status"] = "skip"
        result["message"] = "Testcase %s skipped" % testcase
    if tmp['failure'] > 0:
        result['message'] = "Running testcase %s failed." % testcase
        result['output'] = tmp["output"]
    return result

def get_result_of_testcase(testcase, logfile):
    result = {}

    f = open(logfile, 'r')

    result = {}
    failed = False
    for line in f.readlines():
        if testcase not in line:
            continue

        pattern=" *%s: *\{'auditfail': (\d), 'failure': (\d), 'skipped': (\d), 'calls': (\d)\}" % testcase
        #pattern=" *%s: *\{'calls': (\d), 'failure': (\d), 'skipped': (\d), 'auditfail': (\d)\}" % testcase
        result["output"] = ""
        tmp = re.search(pattern, line)
        if tmp is not None:
            result['auditfail'] = int(tmp.groups()[0])
            result['failure'] = int(tmp.groups()[1])
            result['skip'] = int(tmp.groups()[2])
            result['calls'] = int(tmp.groups()[3])
        else:
            pattern=" *%s: *\{'calls': (\d), 'failure': (\d), 'skipped': (\d), 'auditfail': (\d)\}" % testcase
            tmp = re.search(pattern, line)
            if tmp is not None:
                result['calls'] = int(tmp.groups()[0])
                result['failure'] = int(tmp.groups()[1])
                result['skip'] = int(tmp.groups()[2])
                result['auditfail'] = int(tmp.groups()[3])
        if "FAILED" in line:
            result['output'] = line

    return result

def Run(conf, xmldir):
    logfile = "%s/pacemaker.log" % xmldir
    cluster_env = readClusterConf(conf)

    testcases = []
    #Name of Test Suite
    TestSuiteName = "Running pacemaker-cts"
    #Name of junit xml file
    JunitXML = "junit-pacemakerCTS-ha.xml"

    #Define testcases
    #testcases = [(TestcaseName, TestcaseClass, TestcaseFunction)]
    #eg.
    # ('PacemakerService', 'SetupCluster.service', runPackmakerService)
    #Define function runPackmakerService before using
    cases_def = [("Test Flip", "Flip.PacemakerCTS.service", get_result),
                 ("Test Restart", "Restart.PacemakerCTS.service", get_result),
                 ("Test Stonithd", "Stonithd.PacemakerCTS.service", get_result),
                 ("Test StartOnebyOne", "StartOnebyOne.PacemakerCTS.service", get_result),
                 ("Test SimulStart", "SimulStart.PacemakerCTS.service", get_result),
                 ("Test SimulStop", "SimulStop.PacemakerCTS.service", get_result),
                 ("Test StopOnebyOne", "StopOnebyOne.PacemakerCTS.service", get_result),
                 ("Test RestartOnebyOne", "RestartOnebyOne.PacemakerCTS.service", get_result),
                 ("Test PartialStart", "PartialStart.PacemakerCTS.service", get_result),
                 ("Test Standby", "Standby.PacemakerCTS.service", get_result),
                 ("Test MaintenanceMode", "MaintenanceMode.PacemakerCTS.service", get_result),
                 ("Test ResourceRecover", "ResourceRecover.PacemakerCTS.service", get_result),
                 ("Test ComponentFail", "ComponentFail.PacemakerCTS.service", get_result),
                 ("Test Reattach", "Reattach.PacemakerCTS.service", get_result),
                 ("Test SpecialTest1", "SpecialTest1.PacemakerCTS.service", get_result),
                 ("Test NearQuorumPoint", "NearQuorumPoint.PacemakerCTS.service", get_result),
                 ("Test RemoteBasic", "RemoteBasic.PacemakerCTS.service", get_result),
                 ("Test RemoteStonithd", "RemoteStonithd.PacemakerCTS.service", get_result),
                 ("Test RemoteMigrate", "RemoteMigrate.PacemakerCTS.service", get_result),
                 ("Test RemoteRscFailure","RemoteRscFailure.PacemakerCTS.service", get_result)]

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
