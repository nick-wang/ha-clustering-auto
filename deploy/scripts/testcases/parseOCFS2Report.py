#! /usr/bin/python

import os, sys, re
from junit_xml import TestSuite, TestCase

from library.libJunitXml import assertCase, skipCase
from library.libReadConf import readClusterConf

def get_result(args=None):
    cluster_env = args[0]
    casename = args[1]
    logfile = args[2]

    result = {"status":"fail", "message":"", "output":"", "skipall": False}
    status = ""
    message = ""
    output = ""

    f = open(logfile, 'r')
    for line in f.readlines():
        if casename not in line:
            continue
        row = str(line).split()
        status = row[1]
        break

    if status == "PASSED":
        status = "pass"
        message = "%s: succeed" % casename
        output = "%s: succeed" % casename
    elif status == "FAILED":
        status = "fail"
        message = "%s: failed. Please refer to build log for details." % casename
        output = "%s: failed." % casename
    else:
        status = "skip"
        message = "%s: not scheduled." % casename
        output = "%s: skip." % casename
    
    result["status"] = status
    result["message"] = message
    result["output"] = output

    return result

def parseLog(TestSuiteName, xmlfile, caseset, logfile, cluster_env):
    testcases = []

    #Not necessary to modify the lines below!
    skip_flag = False
    for a_case in caseset:
        case = TestCase(a_case[0], a_case[1])
        testcases.append(case)

        if skip_flag:
            skipCase(case, "This case is not scheduled.")
            continue
        skip_flag = assertCase(case, a_case[2], cluster_env, a_case[0], logfile)

    ts = TestSuite(TestSuiteName, testcases)

    with open(xmlfile, "w") as f:
        ts.to_file(f, [ts])

def parseSingleLog(testreport_dir, cluster_env):

    logfile = "%s/single_report.txt" % testreport_dir
    #Name of Test Suite
    TestSuiteName = "ocfs2 single node test"
    #Name of junit xml file
    JunitXML = "%s/junit-ocfs2-test-single.xml" % testreport_dir

    #Define testcases
    #testcases = [(TestcaseName, TestcaseClass, TestcaseFunction)]
    cases_def = [("create_and_open", "create_and_open.SingleNode.ocfs2test", get_result),
                 ("direct-aio", "directaio.SingleNode.ocfs2test", get_result),
                 ("fill_verify_holes", "fillverifyholes.SingleNode.ocfs2test", get_result),
                 ("rename_write_race", "renamewriterace.SingleNode.ocfs2test", get_result),
                 ("aio-stress", "aiostress.SingleNode.ocfs2test", get_result),
                 ("check_file_size_limits", "filesizelimits.SingleNode.ocfs2test", get_result),
                 ("mmaptruncate", "mmaptruncate.SingleNode.ocfs2test", get_result),
                 ("buildkernel", "buildkernel.SingleNode.ocfs2test", get_result),
                 ("splice", "splice.SingleNode.ocfs2test", get_result),
                 ("sendfile", "sendfile.SingleNode.ocfs2test", get_result),
                 ("mmap", "mmap.SingleNode.ocfs2test", get_result),
                 ("reserve_space", "reserve_space.SingleNode.ocfs2test", get_result),
                 ("inline_data_test", "inline.SingleNode.ocfs2test", get_result),
                 ("xattr_test", "xattr.SingleNode.ocfs2test", get_result),
                 ("reflink_test", "reflink.SingleNode.ocfs2test", get_result),
                 ("mkfs_test", "mkfs.SingleNode.ocfs2test", get_result),
                 ("tunefs_test", "tunefs.SingleNode.ocfs2test", get_result),
                 ("backup_super_test", "backup_super.SingleNode.ocfs2test", get_result),
                 ("filecheck", "filecheck.SingleNode.ocfs2test", get_result)]

    parseLog(TestSuiteName, JunitXML, cases_def, logfile, cluster_env)

def parseMultipleLog(testreport_dir, cluster_env):

    logfile = "%s/multiple_report.txt" % testreport_dir
    #Name of Test Suite
    TestSuiteName = "ocfs2 Multiple nodes test"
    #Name of junit xml file
    JunitXML = "%s/junit-ocfs2-test-multiple.xml" % testreport_dir

    #Define testcases
    #testcases = [(TestcaseName, TestcaseClass, TestcaseFunction)]
    cases_def = [("xattr-test", "xattr.MultipleNodes.ocfs2test", get_result),
                 ("inline-test", "inline.MultipleNodes.ocfs2test", get_result),
                 ("reflink-test", "reflink.MultipleNodes.ocfs2test", get_result),
                 ("write_append_truncate", "write_append_truncate.MultipleNodes.ocfs2test", get_result),
                 ("multi_mmap", "multi_mmap.MultipleNodes.ocfs2test", get_result),
                 ("create_racer", "create_racer.MultipleNodes.ocfs2test", get_result),
                 ("flock_unit", "flock_unit.MultipleNodes.ocfs2test", get_result),
                 ("cross_delete", "cross_delete.MultipleNodes.ocfs2test", get_result),
                 ("open_delete", "open_delete.MultipleNodes.ocfs2test", get_result),
                 ("lvb_torture", "lvb_torture.MultipleNodes.ocfs2test", get_result)]
    parseLog(TestSuiteName, JunitXML, cases_def, logfile, cluster_env)


def main(cluster_conf, testreport_dir):
    cluster_env = readClusterConf(cluster_conf)
    parseSingleLog(testreport_dir, cluster_env)
    parseMultipleLog(testreport_dir, cluster_env)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "Usage: %s <CLUSTER_CONF> <TEST_REPORT_DIR>" % sys.argv[0]
	sys.exit(1)
    main(sys.argv[1], sys.argv[2])
