#!/usr/bin/python3

import argparse
import datetime
import sys, os, time

sys.path.extend(['../', '/var/lib/jenkins-work/ha-share/deploy/scripts/testcases'])
from library.shell import shell

# Required package
PACKAGES=["fio"]

# Fio parameters
IODIRECT    = "1"
IODEPTH     = "20"
IOENGINE    = "libaio"
BS          = "16k"
SIZE        = "2G"
NUMJOBS     = "2"
RUNTIME     = "300"

# testcaes: (CASE_NAME, READ/WRITE)
TEST_CASES = [("SeqRead", "read"),
              ("SeqWrite", "write"),
              ("RandomRead", "randread"),
              ("RandomWrite", "randwrite"),
              ("MixSeqReadWrite", "rw"),
              ("MixRandomReadWrite", "randrw"),
             ]

def parse_argument():
    """
    Parse argument using argparse
    """
    parser = argparse.ArgumentParser(prog=sys.argv[0],
                                     description="DRBD Fio test cases.",
                                     add_help=True,
                                     epilog="""
example: \tdrbdFioTest.py -n 10.67.18.98 -d /dev/drbd4 -o /var/log
""")

    options = parser.add_argument_group('options')
    options.add_argument('-n', '--node', dest='node', metavar='HOSTNAME/IP', required=True,
                         help='Hostname or node of Fio test.')
    options.add_argument('-d', '--device', dest='device', metavar='DEVICE', required=True,
                         help='Fio test device.')
    options.add_argument('-o', '--output-dir', dest='output-dir', default= "./",
                         help='Output director of Fio test result.')

    args = parser.parse_args()

    return vars(args)


def validatePkg(host):
    for pkg in PACKAGES:
       run = shell("ssh root@{0} which {1}".format(host, pkg))
       if run.code != 0:
           print(run.errors())

           run = shell("ssh root@{0} zypper --non-interactive install {1}".format(host, pkg))

           if run.code != 0:
               print(run.errors())
               print("Package/binary {} not found and fail to install.".format(pkg))
               sys.exit(-1)

def fioTest(host="", name="dummy", device="",
            rw="read", output="./dummy"):
    command = "fio -name={0} -filename={1} -direct={2} -iodepth={3} -rw={4} -ioengine={5} -bs={6} -size={7} -numjobs={8} -runtime={9} -thread -group_reporting".format(
        name, device, IODIRECT, IODEPTH, rw,
        IOENGINE, BS, SIZE, NUMJOBS, RUNTIME)

    print(command)
    run = shell("ssh root@{0} {1}".format(host, command))

    if run.output():
        with open(os.path.dirname(output)+"/drbdFioTest-cases", 'a') as fd:
            fd.write('%s:\t%s\n\t%s\n' % (os.path.basename(output),
                                          datetime.datetime.now(), command))

        with open(output, 'w') as fd:
            for line in run.output():
                fd.write('%s\n' % line)

def main():
    """
    Fio command examples:
drbdFioTest-SeqRead-9181:	2021-12-01 16:59:47.875543
	fio -name=SeqRead -filename=/dev/drbd4 -direct=1 -iodepth=20 -rw=read -ioengine=libaio -bs=16k -size=2G -numjobs=2 -runtime=300 -thread -group_reporting
drbdFioTest-SeqWrite-9188:	2021-12-01 17:02:01.096354
	fio -name=SeqWrite -filename=/dev/drbd4 -direct=1 -iodepth=20 -rw=write -ioengine=libaio -bs=16k -size=2G -numjobs=2 -runtime=300 -thread -group_reporting
drbdFioTest-RandomRead-9322:	2021-12-01 17:02:08.435534
	fio -name=RandomRead -filename=/dev/drbd4 -direct=1 -iodepth=20 -rw=randread -ioengine=libaio -bs=16k -size=2G -numjobs=2 -runtime=300 -thread -group_reporting
drbdFioTest-RandomWrite-9329:	2021-12-01 17:07:10.177713
	fio -name=RandomWrite -filename=/dev/drbd4 -direct=1 -iodepth=20 -rw=randwrite -ioengine=libaio -bs=16k -size=2G -numjobs=2 -runtime=300 -thread -group_reporting
drbdFioTest-MixSeqReadWrite-9631:	2021-12-01 17:08:19.742917
	fio -name=MixSeqReadWrite -filename=/dev/drbd4 -direct=1 -iodepth=20 -rw=rw -ioengine=libaio -bs=16k -size=2G -numjobs=2 -runtime=300 -thread -group_reporting
drbdFioTest-MixRandomReadWrite-9700:	2021-12-01 17:13:21.194191
	fio -name=MixRandomReadWrite -filename=/dev/drbd4 -direct=1 -iodepth=20 -rw=randrw -ioengine=libaio -bs=16k -size=2G -numjobs=2 -runtime=300 -thread -group_reporting
    """
    options = parse_argument()

    validatePkg(options["node"])

    dirtemp = options["output-dir"] + "/drbdFioTest"
    if os.path.exists(dirtemp) == False:
        os.makedirs(dirtemp)

    for t in TEST_CASES:
        ts = time.time()
        output = dirtemp + "/drbdFioTest-{}-{}".format(t[0], str(int(ts)%10000))
        fioTest(options["node"], t[0],
                options["device"], t[1], output)
        time.sleep(1)

if __name__ == "__main__":
    main()
