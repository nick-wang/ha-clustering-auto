#! /usr/bin/python

import os, sys, re
from junit_xml import TestSuite, TestCase

from library.libJunitXml import assertCase, skipCase
from library.libReadConf import readClusterConf

def get_result(args=None):
	cluster_env = args[0]
	casename = args[1]
	test_results = args[2]

	result = {"status":"failed", "message":"", "output":"", "skipall": False}
	status = ""
	message = ""
	output = ""

	f = open(test_results, 'r')
	for line in f.readlines():
		if casename != line.split()[0]:
			continue
		status = line.split()[1]
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

def parseLog(TestSuiteName, xmlfile, caseset, test_results, cluster_env):
	testcases = []

	#Not necessary to modify the lines below!
	skip_flag = False
	for a_case in caseset:
		case = TestCase(a_case[0], a_case[1])
		testcases.append(case)

		if skip_flag:
			skipCase(case, "This case is not scheduled.")
			continue
		skip_flag = assertCase(case, a_case[2], cluster_env, a_case[0], test_results)

	ts = TestSuite(TestSuiteName, testcases)

	with open(xmlfile, "w") as f:
		ts.to_file(f, [ts])

def parseTestResults(result_dir, cluster_env):
	test_results = result_dir + '/' + "simplified_reprots"
	if not os.path.isfile(test_results):
		print "WARN: %s not found!" % test_results
		return -1

	#Name of Test Suite
	TestSuiteName = "LVM2 testsuite"
	#Name of Junit xml file
	fullPath = os.path.abspath(test_results);
	TestResultsDir = os.path.dirname(fullPath);
	JunitXML = "%s/junit-lvm2-test-results.xml" % TestResultsDir

	#Define testcases
	#testcases = [(TestcaseName, TestcaseClass, TestcaseFunction)]
	cases_def = []
	name = ''
	f = open(test_results, 'r')
	for line in f.readlines():
		name = line.split()[0]
		caseName = name
		caseClass = "%s.Service" % name
		case = (caseName, caseClass, get_result)
		cases_def.append(case)

	parseLog(TestSuiteName, JunitXML, cases_def, test_results, cluster_env)

def main(cluster_conf, result_dir):
	cluster_env = readClusterConf(cluster_conf)
	parseTestResults(result_dir, cluster_env)

if __name__ == "__main__":
	if len(sys.argv) < 3:
		print "Usage: %s <CLUSTER_CONF> <TEST_RESULTS Dir>" % sys.argv[0]
		sys.exit(1)
	main(sys.argv[1], sys.argv[2])
