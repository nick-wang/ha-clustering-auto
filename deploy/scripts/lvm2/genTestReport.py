#!/usr/bin/python3

# parse the original test_results file, rewrite simplified
# result into another file.

import os, sys

# Put test results into dict.
# The result format is:
#
# 000-basic
# 0 1 1 1 0 0
#
# The first line is test name. The number in the second line
# means: failed, succeeded, runcount, time, interrs, skips
def run(test_results, new_file):
	resDict = {}

	if not os.path.isfile(test_results):
		print("WARN: %s not found!" % test_results)
		exit -1

	f = open(test_results, 'r')
	num = 1
	name = ''
	res = ''
	for line in f.readlines():
		if num % 2 != 0:
			name = line.strip()
		else:
			res = line.split()[0]
			if res == "0":
				res = 'PASSED'
			else:
				res = 'FAILED'
			resDict[name] = res
		num += 1
	f.close()

	f = open(new_file, 'w')
	for name in resDict.keys():
		line = name + ' ' + resDict[name] + '\n'
		f.write(line)
	f.close()

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("Usage: %s <test_results file> <new file>" % sys.argv[0])
		sys.exit(1)

	run(sys.argv[1], sys.argv[2])
