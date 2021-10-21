#!/usr/bin/python3

import sys, os
import time

def recordInfo(cmd, f):
    '''
    Record command output to file before/after function
    '''
    def decorator(func):
        def wrapper(*args, **kargs):
            text = []
            text.append("Before run function {}():\n".format(func.__name__))
            text.append("Rum command: {}\n".format(cmd))
            text.append("--------\n")
            t_start = time.time()
            text.extend(os.popen(cmd).readlines())
            value = func(*args, **kargs)
            t_end = time.time()
            text.append("--------\n")
            text.append("Done testing {}() in {}.\n\n".format(func.__name__, t_end - t_start))

            fd = open(f, "a")
            fd.writelines(text)
            fd.close()

            return value
        return wrapper
    return decorator

def readClusterConf(conf):
    '''
    This is a library to read cluster config file.
    '''
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
    test(sys.argv[1])
