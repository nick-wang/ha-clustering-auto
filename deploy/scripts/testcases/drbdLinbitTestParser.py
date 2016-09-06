#!/usr/bin/python

import sys, os, re
import yaml

from junit_xml import TestSuite, TestCase

from library.libJunitXml import assertCase, skipCase
from library.libReadConf import readClusterConf

# Define test cases and classify
prefix = "LinbitTest."
CLASSIFY = (prefix + "nodefine", prefix + "performance",
            prefix + "exception", prefix + "extra",
            prefix +  "basic")
TESTCASES = {"connect": CLASSIFY[4],
             "initial-resync": CLASSIFY[4],
             "latency": CLASSIFY[4],
             "misaligned-bio": CLASSIFY[1],
             "switch-primaries": CLASSIFY[4],
             "ref-count": CLASSIFY[4],
             "add-connect-delete": CLASSIFY[4],
             "add-path-multiple-times": CLASSIFY[4],
             "ahead-behind.KNOWN": CLASSIFY[1],
             "resize.KNOWN": CLASSIFY[4],
             "resync-never-connected.KNOWN": CLASSIFY[2],
             "diskless": CLASSIFY[2],
             "attach-detach.KNOWN": CLASSIFY[4],
             "multi-path": CLASSIFY[3],
             "compat-with-84": CLASSIFY[3],
             "multiple-devices.KNOWN": CLASSIFY[3],
             "tl_restart-stress.KNOWN": CLASSIFY[1],
            }

def readFromYaml(yml_file):
    # yaml example:
    #   connect:
    #     error: false
    #     isdirty: false
    #     message: null
    #     nodes: 0
    #     output: null
    #     result: PASSED
    #   initial-resync:
    #     error: false
    #     isdirty: false
    #     message: null
    #     nodes: 0
    #     output: null
    #     result: PASSED

    with open(yml_file, "r") as fd:
        result_list=yaml.load(fd)

    # return the hash list
    return result_list

def parseResult(args=None):
    message = ""
    output = ""
    result = {"status":"fail", "message":"", "output":"", "skipall": False}

    cluster_env = args[0]
    casename = args[1]
    r_hash = args[2]

    if r_hash["isdirty"]:
        result["message"] = "Env not clean before running %s.\n" % casename

    if r_hash["error"]:
        result["message"] += r_hash["message"]
        result["output"] = r_hash["result"]
    else:
        result["status"] = "pass"

    return result


def Run(conf, xmldir):
    cluster_env = readClusterConf(conf)

    testcases = []
    #Name of Test Suite
    TestSuiteName = "Linbit DRBD Test"
    #Name of junit xml file
    JunitXML = "junit-linbit-drbd-test.xml"

    yml_file = "%s/Linbit-drbd-test.yml" % xmldir
    results = readFromYaml(yml_file)

    #Define testcases
    #testcases = [(TestcaseName, TestcaseClass, TestcaseFunction)]
    #eg.
    # ('PacemakerService', 'SetupCluster.service', runPackmakerService)
    #Define function runPackmakerService before using
    cases_def = []
    for c_name in results.keys():
        cases_def.append( (c_name, TESTCASES.get(c_name, CLASSIFY[0]), 
                           parseResult) )

    #Not necessary to modify the lines below!
    skip_flag = False
    for a_case in cases_def:
        case = TestCase(a_case[0], a_case[1])
        testcases.append(case)
        if skip_flag:
            skipCase(case, "Can not test!",
                     "Case is skipped due to previous errors.")
            continue
        skip_flag = assertCase(case, a_case[2], cluster_env, a_case[0], results[a_case[0]])

    ts = TestSuite(TestSuiteName, testcases)

    with open(xmldir+"/"+JunitXML, "w") as f:
        ts.to_file(f, [ts])

if __name__ == "__main__":
    Run(sys.argv[1], sys.argv[2])
