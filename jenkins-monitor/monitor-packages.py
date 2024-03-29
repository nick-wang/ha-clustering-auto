#!/usr/bin/python3
#http://download.suse.de/ibs/SUSE:/SLE-12-SP2:/GA/standard/x86_64/

import re, os, urllib.request, sys
import getopt
support_schemas = {'pacemaker':
                       ('pacemaker', 'corosync'),
                   'drbd':
                       ('drbd', 'drbd-utils', 'drbd-kmp-default'),
                   'cluster-md':
                       ('mdadm', 'cluster-md-kmp-default'),
                   'ocfs2':
                       ('ocfs2-tools', 'libdlm', 'ocfs2-kmp-default', 'dlm-kmp-default'),
                  }

module = 'pacemaker'
packages_monitoring = ''
proj_name = ""
dir_name = ""
dummy_dir = "/var/lib/jenkins-dummy/pkgs-change/"

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
    f = open(dummy_dir + filename,'w')
    content=""
    for package in packages:
        content = content + package + "\n"
    f.write(content)
    f.close()

def get_package_info():
    filename = "%s_package_info" % proj_name
    print("Packages info saved in %s" % (dummy_dir + filename))

    if os.path.isdir(dummy_dir):
        if os.path.exists(dummy_dir + filename):
            f = open(dummy_dir + filename)
            return f.read().split()
    elif os.path.isfile(dummy_dir):
        os.unlink(dummy_dir)
        os.mkdir(dummy_dir)
    else:
        os.makedirs(dummy_dir)

    return None

def getName(rpm):
    pattern = "(.*)-(\d+(\.[\w\+\~]+)+)-((\d+\.)+)(\w+)\.rpm"
    tmp = re.match(pattern, rpm)

    if tmp is not None:
        name=tmp.groups()[0]
        return name

    print("Fail to parse: %s" % rpm)
    return None

def need_update(old_packages, new_packages):
    need_updated = {}
    for old_package in old_packages:
        for new_package in new_packages:
            if new_package == old_package:
                break
            elif getName(old_package) == getName(new_package):
                need_updated[old_package] = new_package
                break
            else:
                continue
        else:
            print(old_package + " is not in the new repo.")

    for new_package in new_packages:
        p_name = getName(new_package)

        for old_package in old_packages:
            if p_name == getName(old_package):
                break
        else:
            #print("New record: " + new_package)
            if "NEW" in need_updated:
                need_updated["NEW"].append(new_package)
            else:
                need_updated["NEW"] = [new_package]

    return need_updated

def main(url):
    global packages_monitoring
    #response=urllib.request.urlopen('http://download.suse.de/ibs/SUSE:/SLE-12-SP2:/GA/standard/x86_64/')
    #response=urllib.request.urlopen('http://10.67.160.200/SLP/openSUSE-Tumbleweed/latest/x86_64/')
    try:
        response=urllib.request.urlopen(url)
        # Use decode/str since python3 will read as bytes by default
        html = response.read().decode('utf-8')
    except Exception as e:
        print("wrong url %s" % url)
        print(e)
        usage()
        sys.exit(-1)
    if packages_monitoring == '':
        packages_monitoring = support_schemas[module]

    old_packages = get_package_info()
    new_packages = get_all_packages(html)
    need_updated = {}

    if old_packages is None:
        print('-----------------------')
        print("Initializing the packages:")
        for new_package in new_packages:
            print(new_package)
        print('-----------------------')
        save_package_info(html)
        sys.exit(0)

    elif len(new_packages) > 0:
        need_updated = need_update(old_packages, new_packages)
        if len(need_updated) > 0:
            print("-----------------------")
            print("please update packages:")
            for old_package in list(need_updated.keys()):
                if old_package != "NEW":
                    print("update %s to %s" %(old_package, need_updated[old_package]))
                else:
                    for new_record in need_updated[old_package]:
                        print("new record %s" % new_record)
            print("-----------------------")
            save_package_info(html)
            sys.exit(0)

    print("do not update")
    sys.exit(1)

def usage():
    print("Usage:")
    print("./monitor.py -u <url> -m <module> -P <project_name> -D <job_name> (-p <packages>)")
    print("\tIf gives -p <packages>, then -m <module> will be ignored.")
    print("\tIf gives -D <job_name>, -P <project_name> can be omitted.")
    print("\tExample:")
    print("\t\t./monitor-packages.py  -u 'http://10.67.160.200/SLP/openSUSE-Tumbleweed/latest/x86_64/' -P dummy -p 'kernel-default vim wicked'")
    sys.exit(3)

if __name__ == "__main__":
    url = ""
    try:
        opts, args = getopt.getopt(sys.argv[1:], "u:p:m:P:D:")
    except getopt.GetoptError:
        print("Get options Error!")
        sys.exit(2)
    for opt, value in opts:
        if opt in ("-u", "--url"):
            url = value.strip()
        # If packages give, ignore the module
        elif opt in ("-p", "--packages"):
            packages_monitoring = value.split()
        elif opt in ("-m", "--module"):
            module = value.strip()
        # Could use "JOB_BASE_NAME" for proj_name
        elif opt in ("-P", "--project"):
            proj_name = value.strip()
        # Could use "JOB_NAME" for dir_name
        elif opt in ("-D", "--dirname"):
            dir_name = value.strip() + "/"
            dummy_dir += dir_name
        else:
            usage()

    if dir_name != "" and proj_name == "":
        proj_name = dir_name.split("/")[-2]

    main(url)
