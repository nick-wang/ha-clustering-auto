#!/usr/bin/env python2

import sys
if sys.version_info[0] < 3:
    import urllib2 as urllib
else:
    import urllib.request as urllib

import argparse
import pprint
import re
import os

# <img src="/icons/unknown.gif" alt="[   ]"> <a href="openSUSE-Tumbleweed-DVD-x86_64-Snapshot20200309-Media.iso">openSUSE-Tumbleweed-DVD-x86_64-Snapshot20200309-Media.iso</a>         2020-03-10 23:03  4.3G
HTML_FORMAT = '<a href=".*">({})</a>'

Default = {
    "URL": "http://mirror.suse.asia/dist/install/openSUSE-Tumbleweed/iso/",
    # The inner pattern need able to compare
    "Pattern" : "openSUSE-Tumbleweed-DVD-x86_64-Snapshot([0-9]*)-Media.iso",
    "Location" : "/tmp/downloads",
    "Mount" : "/mnt/ISOs",
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

def download_all(resources, location, remove_old=True):
    os.makedirs(loction, exist_ok=True)

    #Starting download new resources
    #Check existing
    #Remove the one not in the list


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
    parser.add_argument('-r', '--remove', metavar='remove', type=str,
                        help="Remove old resources if exist.", default=Default['Location'])
    parser.add_argument('-m', '--mount-point', metavar='mount', type=str,
                        help="The folder of mount point.", default=Default['Mount'])

    args = parser.parse_args()

    resource_list = retrieveResource(args.url, args.pattern)

    if args.dry_run:
        for res in resource_list:
            print("Find resources: %s" % res)
            return

    resoures = select(resource_list, args.numbers)

    download_all(resources, args.location)

    #mount_all_isos(resources, args.mount)


def test():
    a = Resource(Default["URL"], Default["Pattern"], 333)
    b = Resource(Default["URL"], Default["Pattern"], 323)
    c = Resource(Default["URL"], Default["Pattern"])
    d = Resource(Default["URL"], Default["Pattern"], 393)

    resource_list = [a, b, c, d]

    resources = select(resource_list, 3)

    for res in resources:
        pprint.pprint(res.value)


if __name__ == "__main__":
    #test()
    main()
