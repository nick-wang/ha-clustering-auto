#!/usr/bin/python3

import sys
if sys.version_info[0] < 3:
    import urllib2 as urllib
else:
    import urllib.request as urllib

import argparse
import re
import os
import shutil
import glob

# <img src="/icons/folder.gif" alt="[DIR]"> <a href="SLE-15-SP4-Full-Alpha-202109-LATEST/">SLE-15-SP4-Full-Alpha-202109-LATEST/</a>                             2021-09-29 19:52    -
HTML_FORMAT = '<a href="({})">.*</a>'
BUILD_NUM_PATTERN = ".*-Build([0-9\.]+)-.*"
REPO_POSTFIX = "/x86_64/DVD1/"

FILE_ROOT="/var/lib/jenkins-dummy/build-change/"

Default = {
    "URL": "http://mirror.suse.asia/dist/install/SLP/",
    # The inner pattern need able to compare by library re
    "Pattern" : "SLE-15-SP4-Full-\w+(-\d+)?-LATEST/",
    "File" : "/x86_64/DVD1/media.1/media",
    "JobLocation" : "dummy/project/version/name",
    # Record file should be like /var/lib/jenkins-dummy/build-change/${JOB_NAME}/${BUILD_NUMBER}/record
    "Record" : "",
}

def cmp_version(v1, v2):
    '''
    Input v1, v2 as string
    '''
    list1 = v1.split(".")
    list2 = v2.split(".")

    v1_integer = int(list1[0])
    v2_integer = int(list2[0])

    if v1_integer > v2_integer:
        return True
    elif v1_integer < v2_integer:
        return False
    else:
        v1_decimal = 0 if len(list1) == 1 else int(list1[1])
        v2_decimal = 0 if len(list2) == 1 else int(list2[1])

        if v1_decimal >= v2_decimal:
            return True
        else:
            return False

class Resource:
    def __init__(self, url, name, file):
        # name: SLE-15-SP4-Full-Alpha-202109-LATEST/
        self.url = url
        self.name = name
        self.file = file
        self.repo = url + "/" + name + REPO_POSTFIX
        self.full = url + "/" + name + "/" + file
        self.version = "0"

        page = urllib.urlopen(self.full)
        # use str() because python3 will make line in bytes
        filelines = [line.decode('utf-8').strip() for line in page.readlines()]
        page.close()

        for line in filelines:
            reg = re.search(BUILD_NUM_PATTERN, line)
            if reg is not None:
                #print(reg.groups())
                self.version = reg.groups()[0]

    def __cmp__(self, res2):
        return cmp_version(self.version, res2.version)

    def __repr__(self):
        return "%s" % (self.name.replace("/",""))

    def getVersion(self):
        return self.version

def retrieveResource(url, pattern, file):
    page = urllib.urlopen(url)
    # use str() because python3 will make line in bytes
    filelines = [line.decode('utf-8').strip() for line in page.readlines()]
    page.close()

    res_list = []

    pa = HTML_FORMAT.format(pattern)
    for line in filelines:
        reg = re.search(pa, line)
        if reg is not None:
            #print(line)
            #print(reg.groups())
            newRes = Resource(url, reg.groups()[0], file)
            res_list.append(newRes)

    return res_list

def cmpFunction(res):
    return res.version

def select(resource_list, count=1):
    result = []
    # Sorted from latest to old
    sort_list = sorted(resource_list, key=cmpFunction, reverse=True)
    length = len(resource_list)

    for i in range(min(count, length)):
        result.append(sort_list[i])

    return result

def writeNew(path, res):
    os.makedirs(path, exist_ok=True)

    fd = open(path + "sle_newbuild", "w")
    fd.writelines([res.getVersion()])
    fd.close()

def recordBuild(f, res):
    os.makedirs(os.path.dirname(f), exist_ok=True)

    info = []
    info.append("URL=%s\n" % res.repo)
    info.append("NAME=%s\n" % res.name.strip("/"))

    print("\nRecord Build name and url to %s" % f)
    print("%s%s" % (info[0], info[1]))

    fd = open(f, "w")
    fd.writelines(info)
    fd.close()

def main():
    parser = argparse.ArgumentParser(description="script to SLE monitor build change of url pattern",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-d', '--dry-run', dest='dry_run', action='store_true',
                        help="Only check and list the latest one.")
    parser.add_argument('-c', '--not-clean', dest='clean', action='store_false',
                        help="Clean the old builds record.")
    parser.add_argument('-u', '--url', metavar='url', type=str,
                        help="URL of the repo to check.", default=Default["URL"])
    parser.add_argument('-p', '--pattern', metavar='pattern', type=str,
                        help="pattern of image", default=Default["Pattern"])
    parser.add_argument('-f', '--file', metavar='file', type=str,
                        help="The file of the media file in ISO.", default=Default["File"])
    parser.add_argument('-l', '--location', metavar='location', type=str,
                        help="The location to store comparison job file.", default=Default["JobLocation"])
    parser.add_argument('-r', '--record', metavar='record', type=str,
                        help="The record file of URL and build infor.", default=Default["Record"])

    args = parser.parse_args()

    resource_list = retrieveResource(args.url, args.pattern, args.file)
    if len(resource_list) == 0:
        print("Didn't match any resource.")
        exit(-1)

    if args.dry_run:
        for res in resource_list:
            print("Find resources: %s with version %s" % (res, res.getVersion()))
        exit(-2)

    latest_res = select(resource_list)[0]
    print("The latest %s with version %s" % (latest_res, latest_res.getVersion()))

    path = FILE_ROOT + "/" + args.location + "/"
    print("\nRecord information in folder: %s" % path)
    writeNew(path, latest_res)

    if args.clean:
        print("\nClean the old builds record in folder: %s" % path)

        dirs = glob.glob(path + "[0-9]*")

        for d in dirs:
            shutil.rmtree(d)

    args.record = args.record.strip('"')

    if not os.path.exists(path + "sle_build"):
        shutil.move(path + "sle_newbuild", path + "sle_build")
        print("First run.")
        if len(args.record) != 0:
            recordBuild(args.record, latest_res)
        exit(0)
    else:
        fd = open(path + "sle_build")
        lines = [ l.strip() for l in fd.readlines() ]
        fd.close()

        if cmp_version(lines[0], latest_res.getVersion()):
            print("Build number didn't increase, origin is %s. Do nothing." % lines[0])
            exit(1)
        else:
            shutil.move(path + "sle_newbuild", path + "sle_build")
            print("New image Build number has changed from %s to %s." % (lines[0], latest_res.getVersion()))
            if len(args.record) != 0:
                recordBuild(args.record, latest_res)
            exit(0)

if __name__ == "__main__":
    #./monitor-newbuild.py -l ${JOB_NAME} -p "SLE-15-SP4-Full-\w+(-\d+)?-LATEST/" -r "${RECORD_FILE}"
    # Put `RECORD_FILE=/var/lib/jenkins-dummy/build-change/${JOB_NAME}/${BUILD_NUMBER}/record`
    # In Jenkins multijob predefined parameters
    # source the ${RECORD_FILE} will set the ENV
    main()
