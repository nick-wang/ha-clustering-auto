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
HTML_FORMAT = '<a href=".*">({})</a>'

Default = {
    "URL": "http://mirror.suse.asia/dist/install/openSUSE-Tumbleweed/iso/",
    # The inner pattern need able to compare
    "Pattern" : "openSUSE-Tumbleweed-DVD-x86_64-Snapshot([0-9]*)-Media.iso",
    "Location" : "/tmp/downloads/",
    "Mount" : "/mnt/ISOs/",
}


class Resource:
    def __init__(self, url, name, value=0):
        # name: openSUSE-Tumbleweed-DVD-x86_64-Snapshot20200309-Media.iso
        self.url = url
        self.name = name
        self.value = value

        self.type = name.split(".")[-1]

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
    sort_list = sorted(resource_list, key=cmpFunction, reverse=True)

    for i in range(count):
        result.append(sort_list[i])

    return result

def download_all(resources, location):
    if not os.path.exists(location):
        os.makedirs(location)

    #Starting download new resources
    for res in resources:
        if os.path.exists(os.path.abspath(location) + "/" + res.name):
            print("A file with same name '%s' exist in '%s'" % (res.getMedia(),
                                                               os.path.abspath(location)))
            continue

        response = urllib.urlopen(res.getMedia())
        data = response.read()

        print("Start to download: %s" % res.getMedia())
        print("\t===Downloading %s ===" % datetime.datetime.now())
        _file = open(os.path.join(os.path.abspath(location), res.name), "wb")
        _file.write(data)
        _file.close()
        print("\t===Finish download %s ===\n" % datetime.datetime.now())

    #TODO: verification md5sum?

def mount_all_isos(resources, location, mount_point):
    for res in resources:
        if res.type != "iso":
            continue

        src = os.path.join(os.path.abspath(location), res.name)

        m_dir = os.path.join(os.path.abspath(mount_point), res.value)

        #print("Mount iso: %s to %s" % (src, m_dir))
        utils.mount_iso(src, m_dir, create_dir=True)

def found_old(resources, location, pattern="*"):
    os.chdir(location)

    pattern = pattern.replace("(", "").replace(")", "")

    flist = glob.glob(pattern)
    print(flist)

    outdate = []
    for f in flist:
        for res in resources:
            if f == res.name:
                break
        else:
            # The resouces need remove doesn't need url and value
            outdate.append(Resource("", f, 0))

    # TODO: umount if is iso type
    print("Found obsolete resources:")
    pprint.pprint(outdate)
    return outdate

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
                        help="The lastest (numbers) iso if available.", default=1)
    parser.add_argument('-l', '--location', metavar='location', type=str,
                        help="The folder for download resources.", default=Default['Location'])
    parser.add_argument('-r', '--remove', dest='remove', action='store_true',
                        help="Remove old resources if exist.")
    parser.add_argument('-m', '--mount-point', dest='mount', metavar='mount', type=str,
                        help="The folder of mount point.", default=Default['Mount'])

    args = parser.parse_args()

    resource_list = retrieveResource(args.url, args.pattern)

    if args.dry_run:
        for res in resource_list:
            print("Find resources: %s" % res)
            return

    resources = select(resource_list, args.numbers)

    download_all(resources, args.location)

    mount_all_isos(resources, args.location, args.mount)

    old_res = []
    if args.remove:
        old_res = found_old(resources, args.location, args.pattern)
        #umount_and_delete_old(old, args.location, args.mount)

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
