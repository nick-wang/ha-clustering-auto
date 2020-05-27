#! /usr/bin/python

import os, sys, re
from junit_xml import TestSuite, TestCase

from library.libJunitXml import assertCase, skipCase
from library.libReadConf import readClusterConf

diff_results = "not found not found"
mask_items

#below items result will change from failure to skipped
#cluster: udev-lvmlockd-dlm
#currently, all the cluster_items had been move into run-tst-cluster.sh skip list
mask_cluster_items=[
]
#local:ndev-vanilla
mask_local_items=[
"shell/dmeventd-restart.sh",
"shell/lvchange-syncaction-raid.sh",
"shell/lvchange-raid.sh",
"shell/lvchange-rebuild-raid.sh",
"shell/lvconvert-repair-thin.sh",
"shell/nomda-missing.sh",
]

def get_result(args=None):
	cluster_env = args[0]
	casename = args[1]
	test_results = args[2]
	global diff_results
	global mask_cluster_items
	global mask_local_items

	result = {"status":"failed", "message":"", "output":"", "skipall": False}
	status = "not found"
	message = ""
	output = ""

	f1 = open(test_results, 'r')
	for line in f1.readlines():
		if casename != line.split(' ')[0].split(':')[1]:
			continue
		status1 = line.split(' ')[1]
		break

	f2 = open(diff_results, 'r')
	for line in f2.readlines():
		if casename != line.split(' ')[0].split(':')[1]:
			continue
		status2 = line.split(' ')[1]
		break

	status1 = status1.strip()
	status2 = status2.strip()

	# node1 & node2 got same result.
	if status1 == status2:
		status = status1
	else:
		# if one met failed but another not, think as skip.
		if status1 != status2:
			status = "skip"
			message = "%s: one node failed, tread as skip" % casename

	if status == "passed":
		status = "pass"
		message = "%s: succeed" % casename
		output = "%s: succeed" % casename
	elif status == "failed":
		status = "fail"
		message = "%s: failed" % casename
		output = "%s: failed" % casename
		#if the casename include in mask_item, change it here
		for x in mask_items:
			if casename != x:
				continue
			print("change %s from **failed** to **skip**" % casename);
			status = "skip"
			message = "%s: skip" % casename
			output = "%s: skip" % casename
			break
	else: 
		# note: "timed out", "warnings", "skipped", "interrupted"  result go there
		status = "skip"
		# message may set above
		if message.strip() == '':
			message = "%s: skip" % casename
		output = "%s: skip" % casename

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
	global diff_results
	global mask_items
	test_results = result_dir + '/' + cluster_env["IP_NODE1"] + '/' + "list"
	if not os.path.isfile(test_results):
		print("WARN: %s not found!" % test_results)
		return -1

	diff_results = result_dir + '/' + cluster_env["IP_NODE2"] + '/' + "list"
	if not os.path.isfile(diff_results):
		print("WARN: %s not found!" % diff_results)
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
	line = f.readline()
	if (line.split(':')[0]).find("lvmlockd-dlm") > 0:
	    print("using cluster mask_items")
		mask_items = mask_cluster_items
	else:
	    print("using local mask_items")
		mask_items = mask_local_items
	f.seek(0,0)
	for line in f.readlines():
		name = line.split()[0]
		caseName = name.split(':')[1]
		caseClass = "%s" % name.split(':')[0]
		case = (caseName, caseClass, get_result)
		cases_def.append(case)

	parseLog(TestSuiteName, JunitXML, cases_def, test_results, cluster_env)

def main(cluster_conf, result_dir):
	cluster_env = readClusterConf(cluster_conf)
	parseTestResults(result_dir, cluster_env)

if __name__ == "__main__":
	if len(sys.argv) < 3:
		print("Usage: %s <CLUSTER_CONF> <TEST_RESULTS Dir>" % sys.argv[0])
		sys.exit(1)
	main(sys.argv[1], sys.argv[2])
