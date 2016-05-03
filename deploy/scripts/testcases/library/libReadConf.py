#!/usr/bin/python

import sys

def readClusterConf(conf):
    fd = open(conf, "r")
    lines = [ x.strip() for x in fd.readlines() ]
    fd.close()

    temp = {}
    for line in lines:
        if line == "":
            continue
        temp[line.split("=")[0]] = line.split("=")[1]

    return temp

def test(conf):
    print(readClusterConf(conf))

if __name__ == "__main__":
    '''
        This is a library to read cluster config file.
    '''
    test(sys.argv[1])
