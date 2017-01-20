#! /usr/bin/python
#http://download.suse.de/ibs/SUSE:/SLE-12-SP2:/GA/standard/x86_64/

import re, os, urllib2, sys
import getopt
support_schemas = {'pacemaker':
                       ('pacemaker', 'corosync'),
                   'drbd':
                       ('drbd', 'drbd-utils', 'kernel-default'),
                   'cluster-md':
                       ('mdadm', 'cluster-md-kmp-default', 'kernel-default'),
                  }

module = 'pacemaker'
packages_monitoring = ''
proj_name = ""
dummy_dir = "/tmp/jenkins-dummy/pkgs-change/"

def isTheRPM(package):
    #version=re.groups()[0]
    #release=tmp.groups()[2][0:-1]
    #arch=tmp.groups()[-1]
    if not package.endswith('rpm'):
        return False
    pattern="%s-(\d+(\.[\w\+]+)+)-((\d+\.)+)(\w+)\.rpm"

    for pkg in packages_monitoring:
        pa = re.compile(pattern % pkg)
        if pa.match(package):
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
    global packages_monitoring
    #response=urllib2.urlopen('http://download.suse.de/ibs/SUSE:/SLE-12-SP2:/GA/standard/x86_64/')
    try:
        response=urllib2.urlopen(url)
        html = response.read()
    except Exception, e:
        print "wrong url %s" % url
        print e
        sys.exit(-1)
    if packages_monitoring == '':
        packages_monitoring = support_schemas[module]

    old_packages = get_package_info()
    new_packages = get_all_packages(html)
    need_updated = {}

    if old_packages is None:
        print '-----------------------'
        print "Initializing the packages:"
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
                if old_package != "NEW":
                    print "update %s to %s" %(old_package, need_updated[old_package])
                else:
                    for new_record in need_updated[old_package]:
                        print "new record %s" % new_record
            print "-----------------------"
            save_package_info(html)
            sys.exit(0)

    print "do not update"
    sys.exit(1)

def usage():
    print "./monitor.py -u <url> -m <module> -P <project_name> (-p <packages>)"
    sys.exit(3)

if __name__ == "__main__":
    url = ""
    try:
        opts, args = getopt.getopt(sys.argv[1:], "u:p:m:P:")
    except getopt.GetoptError:
        print "Get options Error!"
        sys.exit(2)
    for opt, value in opts:
        if opt in ("-u", "--url"):
            url = value.strip()
        elif opt in ("-p", "--packages"):
            packages_monitoring = value.split()
        elif opt in ("-m", "--module"):
            module = value.strip()
        elif opt in ("-P", "--project"):
            proj_name = value.strip()
        else:
            usage()

    main(url)
