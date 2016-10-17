#http://download.suse.de/ibs/SUSE:/SLE-12-SP2:/GA/standard/x86_64/
import re, os, urllib2, sys
#pacemaker-1.1.15-17-x86_64.rpm
#corosync-2.3.5-4.2.x86_64.rpm
#patterns=['pacemaker-(\d)','corosync-(\d)+']
patterns=['^pacemaker-(\d)+\.(\d)+\.(\d)+-(\d)+\.(\d)+\.(\w)+\.rpm','^corosync-(\d)+\.(\d)+\.(\d)+-(\d)+\.(\d)+\.\w+\.rpm']

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
        if "pacemaker" in line or "corosync" in line:
            package=line.split('"')[1].split('"')[0]
            if isTheRPM(package) and package not in packages:
                packages.append(package)
    return packages

def save_package_info(html):
    packages = get_all_packages(html)
    f = open('package_info','w')
    content=""
    for package in packages:
        content = content + package + "\n"
    f.write(content)
    f.close()

def get_package_info():
    if os.path.exists('package_info'):
        f = open('package_info')
        return f.read().split()
    return None

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
    if old_packages is None or old_packages != new_packages:
        print "please update"
        save_package_info(html)
        sys.exit(0)
    else:
        print "do not update"
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "usage: ./monitor.py <url>"
        sys.exit(2)
    main(sys.argv[1])
