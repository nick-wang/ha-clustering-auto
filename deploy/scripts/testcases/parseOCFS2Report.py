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
    if not os.path.isfile(logfile):
        print "WARN: %s not found!" % logfile
        return -1

    #Name of Test Suite
    TestSuiteName = "ocfs2 single node test"
    #Name of junit xml file
    JunitXML = "%s/junit-ocfs2-test-single.xml" % testreport_dir

    #Define testcases
    #testcases = [(TestcaseName, TestcaseClass, TestcaseFunction)]
    cases_def = [("create_and_open", "SingleNode.create_and_open", get_result),
                 ("direct-aio", "SingleNode.directaio", get_result),
                 ("fill_verify_holes", "SingleNode.fillverifyholes", get_result),
                 ("rename_write_race", "SingleNode.renamewriterace", get_result),
                 ("aio-stress", "SingleNode.aiostress", get_result),
                 ("check_file_size_limits", "SingleNode.filesizelimits", get_result),
                 ("mmap_truncate", "SingleNode.mmaptruncate", get_result),
                 ("buildkernel", "SingleNode.buildkernel", get_result),
                 ("splice", "SingleNode.splice", get_result),
                 ("sendfile", "SingleNode.sendfile", get_result),
                 ("mmap", "SingleNode.mmap", get_result),
                 ("reserve_space", "SingleNode.reserve_space", get_result),
                 ("inline_data_test", "SingleNode.inline", get_result),
                 ("xattr_test", "SingleNode.xattr", get_result),
                 ("reflink_test", "SingleNode.reflink", get_result),
                 ("mkfs_test", "SingleNode.mkfs", get_result),
                 ("tunefs_test", "SingleNode.tunefs", get_result),
                 ("backup_super_test", "SingleNode.backup_super", get_result),
                 ("filecheck", "SingleNode.filecheck", get_result)]

    parseLog(TestSuiteName, JunitXML, cases_def, logfile, cluster_env)

def parseO2locktopLog(testreport_dir, cluster_env):
    logfile = "%s/o2locktop_report.txt" % testreport_dir
    if not os.path.isfile(logfile):
        print "WARN: %s not found!" % logfile
        return -1

    #Name of Test Suite
    TestSuiteName = "ocfs2 o2locktop test"
    #Name of junit xml file
    JunitXML = "%s/junit-ocfs2-test-o2locktop.xml" % testreport_dir

    #Define testcases
    #testcases = [(TestcaseName, TestcaseClass, TestcaseFunction)]
    cases_def = [("init_test_cases", "O2locktop.init_test_cases", get_result),
                 ("no_file_access", "O2locktop.no_file_access", get_result),
                 ("local_file_access", "O2locktop.local_file_access", get_result),
                 ("remote_file_access", "O2locktop.remote_file_access", get_result),
                 ("multi_file_access", "O2locktop.multi_file_access", get_result),
                 ("uninit_test_cases", "O2locktop.uninit_test_cases", get_result)]

    parseLog(TestSuiteName, JunitXML, cases_def, logfile, cluster_env)

def parseMultipleLog(testreport_dir, cluster_env):

    logfile = "%s/multiple_report.txt" % testreport_dir
    if not os.path.isfile(logfile):
        print "WARN: %s not found!" % logfile
        return -1

    #Name of Test Suite
    TestSuiteName = "ocfs2 Multiple nodes test"
    #Name of junit xml file
    JunitXML = "%s/junit-ocfs2-test-multiple.xml" % testreport_dir

    #Define testcases
    #testcases = [(TestcaseName, TestcaseClass, TestcaseFunction)]
    cases_def = [("xattr-test", "MultipleNodes.xattr", get_result),
                 ("inline-test", "MultipleNodes.inline", get_result),
                 ("reflink-test", "MultipleNodes.reflink", get_result),
                 ("write_append_truncate", "MultipleNodes.write_append_truncate", get_result),
                 ("multi_mmap", "MultipleNodes.multi_mmap", get_result),
                 ("create_racer", "MultipleNodes.create_racer", get_result),
                 ("flock_unit", "MultipleNodes.flock_unit", get_result),
                 ("cross_delete", "MultipleNodes.cross_delete", get_result),
                 ("open_delete", "MultipleNodes.open_delete", get_result),
                 ("lvb_torture", "MultipleNodes.lvb_torture", get_result)]
    parseLog(TestSuiteName, JunitXML, cases_def, logfile, cluster_env)

def parseDiscontigBgSingleLog(testreport_dir, cluster_env):
    logfile = "%s/discontig_bg_single_report.txt" % testreport_dir
    if not os.path.isfile(logfile):
        print "WARN: %s not found!" % logfile
        return -1

    #Name of Test Suite
    TestSuiteName = "ocfs2 discontigous block group single node test"
    #Name of junit xml file
    JunitXML = "%s/junit-ocfs2-test-discontig-bg-single.xml" % testreport_dir

    #Define testcases
    #testcases = [(TestcaseName, TestcaseClass, TestcaseFunction)]
    cases_def = [("inodes_block", "DiscontigBgSingleNode.inodes_block", get_result),
                 ("extent_block", "DiscontigBgSingleNode.extent_block", get_result),
                 ("inline_block", "DiscontigBgSingleNode.inline_block", get_result),
                 ("xattr_block", "DiscontigBgSingleNode.xattr_block", get_result),
                 ("refcount_block", "DiscontigBgSingleNode.refcount_block", get_result)]

    parseLog(TestSuiteName, JunitXML, cases_def, logfile, cluster_env)

def parseDiscontigBgMultipleLog(testreport_dir, cluster_env):

    logfile = "%s/discontig_bg_multiple_report.txt" % testreport_dir
    if not os.path.isfile(logfile):
        print "WARN: %s not found!" % logfile
        return -1

    #Name of Test Suite
    TestSuiteName = "ocfs2 disontigous block group multiple nodes test"
    #Name of junit xml file
    JunitXML = "%s/junit-ocfs2-test-discontig-bg-multiple.xml" % testreport_dir

    #Define testcases
    #testcases = [(TestcaseName, TestcaseClass, TestcaseFunction)]
    cases_def = [("inodes_block", "DiscontigBgMultiNode.inodes_block", get_result),
                 ("extents_block", "DiscontigBgMultiNode.extents_block", get_result),
                 ("xattr_block", "DiscontigBgMultiNode.xattr_block", get_result),
                 ("refcount_block", "DiscontigBgMultiNode.refcount_block", get_result)]

    parseLog(TestSuiteName, JunitXML, cases_def, logfile, cluster_env)

def main(cluster_conf, testreport_dir):
    cluster_env = readClusterConf(cluster_conf)
    parseSingleLog(testreport_dir, cluster_env)
    parseMultipleLog(testreport_dir, cluster_env)
    parseDiscontigBgSingleLog(testreport_dir, cluster_env)
    parseDiscontigBgMultipleLog(testreport_dir, cluster_env)
    parseO2locktopLog(testreport_dir, cluster_env)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "Usage: %s <CLUSTER_CONF> <TEST_REPORT_DIR>" % sys.argv[0]
	sys.exit(1)
    main(sys.argv[1], sys.argv[2])
