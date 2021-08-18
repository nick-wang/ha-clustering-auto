#!/usr/bin/python2

# Obsoleted by download_iso.py

import re, urllib, time, os, getopt
from sys import argv, exit
from multiprocessing import Process, Pipe

#Enable product to monitor
Enable_product = ["sleha", "sle"]
Enable_debug = False

#Configure url and pattern when change
URL = "http://download.suse.de/install/SLE-12-SP1-UNTESTED/"
postfix_sha = ".sha256"
seraddr = "/srv/www/htdocs/"
#Pause between build download
pause_time = 600

sle_pattern = "SLE-12-SP1-Server-DVD-x86_64-Build%s-Media1.iso"
sle_db = ".sle_version"

sleha_pattern = "SLE-12-SP1-HA-DVD-x86_64-Build%s-Media1.iso"
sleha_db = ".sleha_version"

#Support product
PRODUCTS = { "sle": {"pattern": sle_pattern, "database": sle_db, "verify": postfix_sha,
                     "process": "", "iso":"", "pipe": ""},
             "sleha": {"pattern": sleha_pattern, "database": sleha_db, "verify": postfix_sha,
                     "process": "", "iso":"", "pipe": ""} }

run_as_daemon = False

def usage():
	print('''Download and mount daily build ISO tool.\n
Syntax:
%s <options>

Options:
-d(--daemon) Constantly check and download new build.
-h(--help) Show usage.
''' % argv[0])

def DEBUG(string):
	if Enable_debug:
		print(string)
	else:
		pass

def verifySha256(name):
	get_sha = os.popen("/usr/bin/sha256sum ./ISO/%s" % name)
	shaNo = get_sha.readline().split()[0]
	if os.system("grep %s ./ISO/%s >/dev/null 2>&1" % (shaNo, name+postfix_sha)) >> 8 == 0:
		DEBUG("Succeed to verify sha256 number.")
		return True
	else:
		DEBUG("Downloaded ISO is incomplete.")
		return False

def updateRecord(pname, build):
	DEBUG("Record update. product: %s, build: %s" % (pname, build))
	fd = open(PRODUCTS[pname]["database"], "w")
	fd.write(build)
	fd.close()

def downloadFiles(pname, nbuild, conn):
	name = PRODUCTS[pname]["pattern"] % nbuild

	print("Process %d - Start to download: %s." % (PRODUCTS[pname]["process"].pid, URL+name+postfix_sha))
	urllib.urlretrieve(URL+name+postfix_sha, "./ISO/"+name+postfix_sha)

	print("Process %d - Start to download: %s." % (PRODUCTS[pname]["process"].pid, URL+name))
	urllib.urlretrieve(URL+name, "./ISO/"+name)

	if not verifySha256(name):
		conn.send("")
		conn.close()
		return False
	else:
		#Save new downloaded ISO's name
		DEBUG("ISO %s downloaded." % name)
		conn.send(name)
		conn.close()

		updateRecord(pname, nbuild)
		return True

def hasNew(pname, old):
	#Occasionally fail to connect download.suse.de
	while True:
		try:
			urlfd = urllib.urlopen(URL)
		except IOError, e:
			print("urlopen: %s.\nURL is %s." % (e.__str__(), URL))
			time.sleep(20)
		else:
			break

	for line in urlfd.readlines():
		result = re.search(PRODUCTS[pname]["pattern"] % "([0-9]+)", line)
		if result is not None:
			build = result.groups()[0]
			break

	if int(build) > int(old):
		DEBUG("Found new build %s for product %s." % (build, pname))
		return build
	else:
		return ""

def getNewISO(pname):
	try:
		fd = open(PRODUCTS[pname]["database"], "r")
		obuild = fd.readline().strip()
		fd.close()
	except IOError:
		fd = open(PRODUCTS[pname]["database"], "w")
		fd.write("0")
		fd.close()
		obuild = "0"

	nbuild = hasNew(pname, obuild)
	if nbuild != "":
		parent_conn, child_conn = Pipe()
		PRODUCTS[pname]["process"] = Process(target=downloadFiles,
                                             args=(pname, nbuild, child_conn),
                                             name=pname)
		PRODUCTS[pname]["pipe"] = parent_conn
		PRODUCTS[pname]["process"].start()

def mountISO(pname):
	# /srv/www/htdocs/ -> repo/UNTESTED/
	# (seraddr)        -> ISO/download-iso.py
	#                        /xxx.iso
	obsolete_iso = ""
	iso_dir = seraddr+"ISO/"
	mount_dir = seraddr+"repo/UNTESTED/"+PRODUCTS[pname]["pattern"].split("-Build")[0]

	if not os.path.isdir(mount_dir):
		os.mkdir(mount_dir)
	else:
		mount_info = os.popen("mount |grep %s" % mount_dir).readline()
		if mount_info != "":
			DEBUG("Old mount info: %s" % mount_info)
			obsolete_iso = mount_info.split()[0]
			os.system("umount -d %s >/dev/null 2>&1" % mount_dir)

	if os.system("mount -o loop %s %s" % (iso_dir+PRODUCTS[pname]["iso"], mount_dir)) >> 8 == 0:
		DEBUG("Succeed to mount new ISO.")
		if obsolete_iso != "":
			DEBUG("Remove obsolete ISO.")
			os.system("rm -rf %s* >/dev/null 2>&1" % obsolete_iso)
		return True
	else:
		return False

def getOption():
	DEBUG("Options are: %s" % argv[1:])
	global run_as_daemon

	try:
		opts, args = getopt.getopt(argv[1:], "dh", ["help", "daemon"])
	except getopt.GetoptError:
		print("Get options Error!")
		exit(1)

	for opt, value in opts:
		if opt in ("-d", "--daemon"):
			run_as_daemon=True
		elif opt in ("-h", "--help"):
			usage()
		else:
			pass

def main():
	os.chdir(seraddr)

	getOption()

	while True:
		for product in Enable_product:
			getNewISO(product)

		for product in Enable_product:
			if PRODUCTS[product]["process"] != "":
				PRODUCTS[product]["iso"] = PRODUCTS[product]["pipe"].recv()
				PRODUCTS[product]["process"].join()

				#Mount and add repo
				if PRODUCTS[product]["iso"] != "":
					mountISO(product)

				PRODUCTS[product]["process"] = ""

		if not run_as_daemon:
			break
		else:
			time.sleep(pause_time)
			DEBUG("Checking new build...")

	print("Monitor process End.")

if __name__=='__main__':
	main()
