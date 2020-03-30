#!/usr/bin/env python3

import sys
if sys.version_info[0] < 3:
    import urllib2 as urllib
else:
    import urllib.request as urllib

import argparse
import pprint
import re
import os
import datetime
import glob

import utils

# <img src="/icons/unknown.gif" alt="[   ]"> <a href="openSUSE-Tumbleweed-DVD-x86_64-Snapshot20200309-Media.iso">openSUSE-Tumbleweed-DVD-x86_64-Snapshot20200309-Media.iso</a>         2020-03-10 23:03  4.3G
HTML_FORMAT = '<a href="({})">.*</a>'

Default = {
    "URL": "http://mirror.suse.asia/dist/install/openSUSE-Tumbleweed/iso/",
    # The inner pattern need able to compare
    "Pattern" : "openSUSE-Tumbleweed-DVD-x86_64-Snapshot([0-9]*)-Media.iso",
    "Location" : "/tmp/downloads/ISOs/openSUSE-Tumbleweed",
    "Mount" : "/mnt/SLP/openSUSE-Tumbleweed",
    "Verify" : ""
}

verification_bin = {
    "sha256" : "/usr/bin/sha256sum",
}


class Resource:
    def __init__(self, url, name, value=0):
        # name: openSUSE-Tumbleweed-DVD-x86_64-Snapshot20200309-Media.iso
        self.url = url
        self.name = name
        self.value = value

        if "." in name:
            self.type = name.split(".")[-1]
        else:
            self.type = ""

    def __cmp__(self, res2):
        return cmp(self.value, res2.value)

    def __repr__(self):
        return "%s" % (self.name)

    def getValue(self):
        return self.value

    def getMedia(self):
        return self.url + self.name

def retrieveResource(url, pattern):
    page = urllib.urlopen(url)
    # use str() because python3 will make line in bytes
    filelines = [str(line.strip()) for line in page.readlines()]
    page.close()

    res_list = []

    pa = HTML_FORMAT.format(pattern)
    for line in filelines:
        reg = re.search(pa, line)
        if reg is not None:
            #print(reg.groups()[0], reg.groups()[1])
            newRes = Resource(url, reg.groups()[0], reg.groups()[1])
            res_list.append(newRes)

    return res_list

def cmpFunction(res):
    return res.value

def select(resource_list, count):
    result = []
    # Sorted from latest to old
    sort_list = sorted(resource_list, key=cmpFunction, reverse=True)
    length = len(resource_list)

    for i in range(min(count, length)):
        result.append(sort_list[i])

    return result

def verification(name, location, verify):
    if not verification_bin.get(verify):
        print("\tNo (%s) binary to verify the resource.\n" % verify)
        return False

    get_veriNo = os.popen("{bin} {location}/{file} ".format(bin=verification_bin[verify],
                                                         location=location,
                                                         file=name))
    veriNo = get_veriNo.readline().split()[0]

    if os.system("grep %s %s/%s >/dev/null 2>&1" % (veriNo, location,
                                                    name + "." + verify)
                 ) >> 8 == 0:
        print("\tSucceed to verify (%s) number: %s.\n" % (verify, veriNo))
        return True
    else:
        print("\tERROR! Downloaded ISO is incomplete.\n")
        return False

def download_all(resources, location, verify):
    if not os.path.exists(location):
        os.makedirs(location)

    #Starting download new resources
    for res in resources:
        place = os.path.abspath(location) + "/" + res.name
        if os.path.exists(place):
            print("A file with same name '%s' exist in '%s'" % (res.getMedia(),
                                                               os.path.abspath(location)))
            continue

        print("Start to download: %s" % res.getMedia())
        print("\t===Downloading %s ===" % datetime.datetime.now())
        # Using wget instead of urllib2 to download
        #response = urllib.urlopen(res.getMedia())
        #data = response.read()

        #_file = open(os.path.join(os.path.abspath(location), res.name), "wb")
        #_file.write(data)
        #_file.close()
        sh = utils.command("wget -c {url} -P {location}".format(url=res.getMedia(),
                                                                location=location))
        print("\t===Finish download %s ===\n" % datetime.datetime.now())

        if verify != "":
            verfile = res.getMedia() + "." + verify
            print("\tStart to download (%s) verify file: %s" % (verify, verfile))
            sh = utils.command("wget -c {url} -P {location}".format(url=verfile,
                                                                    location=location))
            print("\tFinish download verification file(%s).\n" % verify)
            verification(res.name, location, verify)
            os.remove("%s/%s" % (location, res.name + "." + verify))


def mount_all_isos(resources, location, mount_point):
    for res in resources:
        if res.type != "iso":
            continue

        src = os.path.join(os.path.abspath(location), res.name)

        m_dir = os.path.join(os.path.abspath(mount_point), res.value)

        print("Mount iso: %s to %s" % (src, m_dir))
        utils.mount_iso(src, m_dir, create_dir=True)

    #Create the latest link
    cwd = os.path.abspath((os.curdir))
    os.chdir(mount_point)
    if os.path.exists("latest"):
        os.remove("latest")
    os.symlink(os.path.join(os.path.abspath(mount_point), resources[0].value), "latest")
    os.chdir(cwd)

def umount_and_delete_old(old_res, location, mount_point):
    for res in old_res:
        if res.type != "iso":
            continue

        src = os.path.join(os.path.abspath(location), res.name)
        print("Umount iso: %s" % src)
        if utils.umount_iso(src):
            os.remove(src)
            # The folder "os.path.join(os.path.abspath(mount_point), res.value)"
            # suppose to empty after umount
            os.rmdir(os.path.join(os.path.abspath(mount_point), res.value))
            #import shutil
            #shutil.rmtree(os.path.join(os.path.abspath(mount_point), res.value))

def found_old(resources, numbers, location, pattern="*"):
    newNum = len(resources)
    cwd = os.path.abspath((os.curdir))
    os.chdir(location)

    new_pa = pattern.replace("(", "").replace(")", "")

    flist = glob.glob(new_pa)
    os.chdir(cwd)

    outdate = []
    for f in flist:
        for res in resources:
            if f == res.name:
                break
        else:
            # The resouces need remove doesn't need url
            value = 0
            reg = re.search(pattern, f)
            if reg is not None:
                value = reg.groups()[0]

            outdate.append(Resource("", f, value))

    sort_list = sorted(outdate, key=cmpFunction, reverse=True)
    needNum = numbers - newNum
    oldNum = len(outdate)

    removeRes = []
    if oldNum > needNum:
        delNum = oldNum - needNum

        for i in range(delNum):
            removeRes.append(sort_list.pop())

        print("Found obsolete resources:")
        pprint.pprint(removeRes)

    else:
        print("No need to delete resource. {} needed, {} exist.".
              format(numbers, newNum + oldNum))

    return removeRes

def main():
    parser = argparse.ArgumentParser(description="script to download the latest (n) images/isos",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-d', '--dry-run', dest='dry_run', action='store_true',
                        help="Only check and list the latest one.")
    parser.add_argument('-u', '--url', metavar='url', type=str,
                        help="URL of the repo to check.", default=Default["URL"])
    parser.add_argument('-p', '--pattern', metavar='pattern', type=str,
                        help="pattern of image", default=Default["Pattern"])
    parser.add_argument('-n', '--numbers', metavar='numbers', type=int,
                        help="The lastest (numbers) resources to download/keep.", default=3)
    parser.add_argument('-l', '--location', metavar='location', type=str,
                        help="The folder for download resources.", default=Default['Location'])
    parser.add_argument('-r', '--remove', dest='remove', action='store_true',
                        help="Remove old resources if exist.")
    parser.add_argument('-m', '--mount-point', dest='mount', metavar='mount', type=str,
                        help="The folder of mount point.", default=Default['Mount'])
    parser.add_argument('-c', '--verify', dest='verify', metavar='verify', type=str,
                        help="verification of the download.", default=Default['Verify'])


    args = parser.parse_args()

    resource_list = retrieveResource(args.url, args.pattern)
    if len(resource_list) == 0:
        print("Didn't match any resource.")
        return

    if args.dry_run:
        for res in resource_list:
            print("Find resources: %s" % res)
            return

    resources = select(resource_list, args.numbers)

    download_all(resources, args.location, args.verify)

    mount_all_isos(resources, args.location, args.mount)

    old_res = []
    if args.remove:
        old_res = found_old(resources, args.numbers, args.location, args.pattern)
        umount_and_delete_old(old_res, args.location, args.mount)

def test():
    a = Resource(Default["URL"], Default["Pattern"], 333)
    b = Resource(Default["URL"], Default["Pattern"], 323)
    c = Resource(Default["URL"], Default["Pattern"])
    d = Resource(Default["URL"], Default["Pattern"], 393)
    e = Resource("http://10.67.19.7/cups/", "client.conf")
    f = Resource("http://10.67.19.7/cups/", "command.types")
    g = Resource("http://10.67.19.7/cups/", "cups-browsed.conf")
    h = Resource("http://10.67.19.7/cups/", "cups-files.conf")

    resource_list = [a, b, c, d]

    resources = select(resource_list, 3)
    resources = [e, f, g, h]

    for res in resources:
        pprint.pprint(res.value)

    download_all(resources, "./")


if __name__ == "__main__":
    #test()
    main()
