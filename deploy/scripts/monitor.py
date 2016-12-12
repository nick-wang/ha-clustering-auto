#! /usr/bin/python
#http://download.suse.de/ibs/SUSE:/SLE-12-SP2:/GA/standard/x86_64/

import re, os, urllib2, sys
import getopt
#pacemaker-1.1.15-17-x86_64.rpm
#corosync-2.3.5-4.2.x86_64.rpm
#patterns=['pacemaker-(\d)','corosync-(\d)+']
patterns=['^pacemaker-(\d)+\.(\d)+\.(\d)+-(\d)+\.(\d)+\.(\w)+\.rpm','^corosync-(\d)+\.(\d)+\.(\d)+-(\d)+\.(\d)+\.\w+\.rpm']
packages_monitoring=['pacemaker', 'corosync']
proj_name=""

def isTheRPM(package):
    if not package.endswith('rpm'):
        return False
    for pattern in patterns:
        p = re.compile(pattern)
        if p.match(package):
            return True
    return False

def get_all_packages(html):
    content = html.split()
    packages = []
    for line in content:
        for package in packages_monitoring:
            if package in line:
                package=line.split('"')[1].split('"')[0]
                if isTheRPM(package) and package not in packages:
                    packages.append(package)
    return packages

def save_package_info(html):
    packages = get_all_packages(html)
    filename = "%s_package_info" % proj_name
    f = open(filename,'w')
    content=""
    for package in packages:
        content = content + package + "\n"
    f.write(content)
    f.close()

def get_package_info():
    filename = "%s_package_info" % proj_name
    if os.path.exists(filename):
        f = open(filename)
        return f.read().split()
    return None

def need_update(old_packages, new_packages):
    need_updated = {}
    for old_package in old_packages:
        for new_package in new_packages:
            if new_package == old_package:
                continue
            if old_package.split('-')[0] not in new_package:
                continue
            need_updated[old_package] = new_package
    return need_updated

def main(url):
    #response=urllib2.urlopen('http://download.suse.de/ibs/SUSE:/SLE-12-SP2:/GA/standard/x86_64/')
    try:
        response=urllib2.urlopen(url)
        html = response.read()
    except Exception, e:
        print "wrong url %s" % url
        print e
        sys.exit(-1)
    old_packages = get_package_info()
    new_packages = get_all_packages(html)
    need_updated = {}

    if old_packages is None:
        print '-----------------------'
        print "please update packages:"
        for new_package in new_packages:
            print new_package
        print '-----------------------'
        save_package_info(html)
        sys.exit(0)

    elif len(new_packages) > 0:
        need_updated = need_update(old_packages, new_packages)
        if len(need_updated) > 0:
            print "-----------------------"
            print "please update packages:"
            for old_package in need_updated.keys():
                print "update %s to %s" %(old_package, need_updated[old_package])
            print "-----------------------"
            save_package_info(html)
            sys.exit(0)

    print "do not update"
    sys.exit(1)

def usage():
    print "./monitor.py -u <url> -p <packages> -P <project_name>"
    sys.exit(3)

if __name__ == "__main__":
    url = ""
    try:
        opts, args = getopt.getopt(sys.argv[1:], "u:p:P:")
    except getopt.GetoptError:
        print "Get options Error!"
        sys.exit(2)
    for opt, value in opts:
        if opt in ("-u", "--url"):
            url = value.strip()
        elif opt in ("-p", "--packages"):
            packages_monitoring = value.split()
        elif opt in ("-P", "--project"):
            proj_name = value.strip()
        else:
            usage()

    main(url)
