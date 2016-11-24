#!/usr/bin/python
#
# genTestReport.py <BUILD_LOG_DIR>

import os, sys, subprocess
import re

# how the parse* func works below really depends on what the
# ocfs2-test testing result log looks like...

def parseSingleLog(log, test_report_dir):
	tblLog = {}
	priorLine = ""
	case = ""
	time = ""

	with open(log, "r") as f:
		for line in f:
			if line.find("PASSED") != -1:
				time = re.split(r"\(|\)", line)[1]
				case = priorLine.split()[2]
				tblLog[case] = ["PASSED", time]
			elif line.find("FAILED") != -1:
				time = re.split(r"\(|\)", line)[1]
				case = priorLine.split()[2]
				tblLog[case] = ["FAILED", time]
			else:
				pass
			priorLine = line

	with open(test_report_dir + "/single_report.txt", "w") as f:
		for k, v in tblLog.iteritems():
			row = str(k) + " " + str(v[0]) + " " + str(v[1])
			f.write(row + "\n")

def parseMultipleLog(log, test_report_dir):
	tblLog = {}
	priorLine = ""
	case = ""
	time = ""
	result = ""

	with open(log, "r") as f:
		flag = False
		for line in f:
			# time is in the next line
			if flag:
				time = line.split()[1] + " seconds"
				tblLog[case] = [result, time]
				flag = False
				continue

			if line.find("Passed") != -1:
				case = re.split(r"\.+", line)[0]
				result = "PASSED"
				flag = True
				continue
			elif line.find("Failed") != -1:
				case = re.split(r"\.+", line)[0]
				result = "FAILED"
				flag = True
				continue
			else:
				pass

	with open(test_report_dir + "/multiple_report.txt", "w") as f:
		for k, v in tblLog.iteritems():
			row = str(k) + " " + str(v[0]) + " " + str(v[1])
			f.write(row + "\n")

def parseDiscontigBgSingleLog(log, test_report_dir):
	tblLog = {}
	case = ""
	result = ""

# Example:
# [*] Inodes Block Group Test:       [ PASS ]
	with open(log, "r") as f:
		for line in f:
			if line.find("PASS") != -1:
				case = re.split(r"\s", line)[1].lower() + "_block"
				result = "PASSED"
			elif line.find("FAILED") != -1:
				case = re.split(r"\s", line)[1].lower() + "_block"
				result = "FAILED"
			else:
				continue

			tblLog[case] = [result]

	with open(test_report_dir + "/discontig_bg_single_report.txt", "w") as f:
		for k, v in tblLog.iteritems():
			row = str(k) + " " + str(v[0])
			f.write(row + "\n")

def parseDiscontigBgMultipleLog(log, test_report_dir):
	tblLog = {}
	case = ""
	result = ""

# Example:
# [*] Multi-nodes Inodes Block Group Test:      [ PASS ]
	with open(log, "r") as f:
		for line in f:
			if line.find("PASS") != -1:
				case = re.split(r"\s", line)[2].lower() + "_block"
				result = "PASSED"
			elif line.find("FAILED") != -1:
				case = re.split(r"\s", line)[2].lower + "_block"
				result = "FAILED"
			else:
				continue

			tblLog[case] = [result]

	with open(test_report_dir + "/discontig_bg_multiple_report.txt", "w") as f:
		for k, v in tblLog.iteritems():
			row = str(k) + " " + str(v[0])
			f.write(row + "\n")


def main(dir):
	single_log = ""
	multiple_log = ""
	discontig_bg_single_log=""
	discontig_bg_multiple_log=""

	p = subprocess.Popen(["find", dir, "-name", "single_run.log"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(stdoutdata, stderrdata) = p.communicate()

	if p.returncode == 0:
		single_log = str(stdoutdata).strip()
		print "Single log file: %s" % single_log
	else:
		print stderrdata

	p = subprocess.Popen(["find", dir, "-name", "multiple-run-*.log"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(stdoutdata, stderrdata) = p.communicate()

	if p.returncode == 0:
		multiple_log = str(stdoutdata).strip()
		print "Multiple log file: %s" % multiple_log
	else:
		print stderrdata

	p = subprocess.Popen(["find", dir, "-name", "*discontig-bg-single-run.log"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(stdoutdata, stderrdata) = p.communicate()

	if p.returncode == 0:
		discontig_bg_single_log = str(stdoutdata).strip()
		print "Discontig bg single log file: %s" % discontig_bg_single_log
	else:
		print stderrdata

	p = subprocess.Popen(["find", dir, "-name", "*discontig-bg-multiple-run.log"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(stdoutdata, stderrdata) = p.communicate()

	if p.returncode == 0:
		discontig_bg_multiple_log = str(stdoutdata).strip()
		print "Discontig bg multiple log file: %s" % discontig_bg_multiple_log
	else:
		print stderrdata


	if single_log or multiple_log or discontig_bg_single_log or discontig_bg_multiple_log:
		test_report_dir = dir + "/test_reports/"
		p = subprocess.Popen(["mkdir", "-p", test_report_dir], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(stdoutdata, stderrdata) = p.communicate()

		if p.returncode == 0:
			print "Mkdir -p %s" % test_report_dir
		else:
			print stderrdata

	if single_log:
		parseSingleLog(single_log, test_report_dir)
	if multiple_log:
		parseMultipleLog(multiple_log, test_report_dir)
	if discontig_bg_single_log:
		parseDiscontigBgSingleLog(discontig_bg_single_log, test_report_dir)
	if discontig_bg_multiple_log:
		parseDiscontigBgMultipleLog(discontig_bg_multiple_log, test_report_dir)

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print "Usage: %s <BUILD_LOG_DIR>" % sys.argv[0]
		sys.exit(1)

	main(sys.argv[1])
