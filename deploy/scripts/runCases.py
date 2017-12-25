#!/usr/bin/python3

import sys, getopt, os
from junit_xml import TestSuite, TestCase

def usage():
    print("usage:")
    print("\t./runCases.py -d <output-dir> -f <configuration> -r <runs>")
    sys.exit(1)

def runCases(conf, run_list, output_dir):
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    for run_name in run_list.split():
        os.system("./testcases/%s %s %s" % (run_name, conf, output_dir))

def getOption():
    options = {"configuration": "../cluster_conf", "runs": "", "dir": "../"}

    try:
        opts, args = getopt.getopt(sys.argv[1:], "f:r:d:",
                    ["configuration=", "runs=", "dir="])
    except getopt.GetoptError:
        print("Get options Error!")
        sys.exit(2)

    for opt, value in opts:
        if opt in ("-f", "--configuration"):
            options["configuration"] = value
        elif opt in ("-r", "--runs"):
            options["runs"] = value
        elif opt in ("-d", "--dir"):
            options["dir"] = value
        else:
            usage()

    return options

if __name__ == "__main__":
    options = getOption()
    runCases(options["configuration"], options["runs"], options["dir"])
