#!/usr/bin/env python 
import re, urllib, time
from os import popen, system
from sys import argv
from multiprocessing import Process 

# Usage:
# 1) How to launch
#   Check new ISO for once: ./download-iso.py
#   Insistently check new ISO: ./download-iso.py daemon
# 2) How to configure
#   Enable monitor product in "enable_product" and "PRODUCTS"
#   Add pattern and database file for new product. 
#       like sle_pattern and sle_db

URL = "http://download.suse.de/install/SLE-12-SP1-UNTESTED/"
postfix_sha = ".sha256"

#Pause between build download
pause_time = 120

sle_pattern = "SLE-12-SP1-Server-DVD-x86_64-Build%s-Media1.iso"
sle_db = ".sle_version"

sleha_pattern = "SLE-12-SP1-HA-DVD-x86_64-Build%s-Media1.iso"
sleha_db = ".sleha_version"

#Support product
PRODUCTS = { "sle": {"pattern": sle_pattern, "database": sle_db, "verify": postfix_sha, "process": ""},
             "sleha": {"pattern": sleha_pattern, "database": sleha_db, "verify": postfix_sha, "process": ""} }

#Enable product to monitor
enable_product = ["sle", "sleha"]

def verify_sha256(name):
	getSha = popen("/usr/bin/sha256sum %s" % name)
	shaNo = getSha.readline().split()[0]
	if system("grep %s %s" % (shaNo, name+postfix_sha)) >> 8 == 0:
		return True
	else:
		return False

def update_record(pname, build):
	fd = open(PRODUCTS[pname]["database"], "w")
	fd.write(build)
	fd.close()

def download_files(pname, nbuild):
	name = PRODUCTS[pname]["pattern"] % nbuild

	print "Process %d - Start to download: %s." % (PRODUCTS[pname]["process"].pid, URL+name+postfix_sha,)
	urllib.urlretrieve(URL+name+postfix_sha, name+postfix_sha)
	print "Process %d - Start to download: %s." % (PRODUCTS[pname]["process"].pid, URL+name)
	urllib.urlretrieve(URL+name, name)

	if not verify_sha256(name):
		return False
	else:
		update_record(pname, nbuild)

def hasNew(pname, old):
	urlfd = urllib.urlopen(URL)

	for line in urlfd.readlines():
		result = re.search(PRODUCTS[pname]["pattern"] % "([0-9]+)", line)
		if result is not None:
			build = result.groups()[0]
			break

	if int(build) > int(old):
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
		PRODUCTS[pname]["process"] = Process(target=download_files, 
                                             args=(pname, nbuild),
                                             name=pname)
		PRODUCTS[pname]["process"].start()
		#TODO Add repo
		#TODO old clean ISO env
		#TODO change process back to ""


def main():
	while True:
		for product in enable_product:
			getNewISO(product)

		for product in enable_product:
			if PRODUCTS[product]["process"] != "":
				PRODUCTS[product]["process"].join()

		if len(argv) == 1:
			break
		else:
			time.sleep(pause_time)

	print "Monitor process End."

if __name__=='__main__':
	main()
