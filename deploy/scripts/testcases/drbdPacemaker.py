#!/usr/bin/python3

import sys, os, re
import library.libDRBD as libDRBD

from time import sleep
from junit_xml import TestSuite, TestCase

from library.libJunitXml import assertCase, skipCase
from library.libCommon import readClusterConf, recordInfo

temp = readClusterConf(sys.argv[1])

CMD_WRAPPER = "ssh root@%s {} 2>&1" % temp["IP_NODE1"]
REC_FILE    = sys.argv[2] + "/" + "drbdPacemaker_state.output"

@recordInfo(CMD_WRAPPER.format("drbdadm status all"), REC_FILE)
def configurePacemaker(args=None):
    message = ""
    output = ""
    result = {"status":"fail", "message":"", "output":"", "skipall": False}

    cluster_env = args[0]

    #Own test steps
    resource_lists = []

    lines = os.popen("ssh root@%s crm configure show" % cluster_env["IP_NODE1"]).readlines()

    pa = re.compile("\s*params drbd_resource=([\w-]*)\s+.*")
    for line in lines:
        tmp = re.match(pa, line)
        if tmp is not None:
            resource_lists.append(tmp.groups()[0])

    if len(resource_lists) == 0 :
        message = "No DRBD resource configured in pacemaker."
    else:
        all_lines = "".join(lines)
        for res in resource_lists:
            if re.search("ms ms_%s" % res, all_lines) is None:
                message = "No corresponding ms(%s) resource configured." % res
                output = all_lines
                break
        else:
            result["status"] = "pass"

    #Skipall following test cases when this failed
    if result["status"] == "fail":
        result["skipall"] = True

    result["message"] = message
    result["output"] = output

    return result

@recordInfo(CMD_WRAPPER.format("cat /proc/drbd"), REC_FILE)
def checkDRBDVersion(args=None):
    message = ""
    output = ""
    result = {"status":"fail", "message":"", "output":"", "skipall": False}

    cluster_env = args[0]

    #Own test steps
    ver = ""
    gen = 0
    release = 0

    lines = os.popen("ssh root@%s cat /proc/drbd" % cluster_env["IP_NODE1"]).readlines()
    output = "".join(lines)

    pa = re.compile("^version: ([\d\.]*)-([\d\w]*) .*")
    for line in lines:
        tmp = re.match(pa, line)
        if tmp is not None:
            ver = tmp.groups()[0]
            gen = int(ver.split(".")[0])
            #remove the int(), in case release like 0rc1
            release = tmp.groups()[1]

    if len(ver) == 0 or gen < 8:
        message = "No support DRBD version found."
    else:
        if gen == 8:
            message = "DRBD8(%s) loaded! Check the DRBD module package." % ver
        else:
            result["status"] = "pass"

    #Skipall following test cases when this failed
    if result["status"] == "fail" and len(message) == 0:
        result["skipall"] = True

    result["message"] = message
    result["output"] = output

    return result

@recordInfo(CMD_WRAPPER.format("drbdadm status all"), REC_FILE)
def checkDRBDState(args=None):
    message = ""
    output = ""
    result = {"status":"fail", "message":"", "output":"", "skipall": False}

    cluster_env = args[0]

    #Own test steps
    uptodate_disk = 0
    node_num = libDRBD.getNodesNumber(cluster_env)
    disk_num = libDRBD.getVolumeNumber(cluster_env)

    lines = os.popen("ssh root@%s drbdadm status all" % cluster_env["IP_NODE1"]).readlines()
    pa = re.compile("[ -]disk:UpToDate$")
    for line in lines:
        if re.search(pa, line) is not None:
            uptodate_disk += 1

    if uptodate_disk == ( disk_num * node_num ):
        result["status"] = "pass"
    else:
        message = "Only %d out of %d is UpToDate." % (uptodate_disk, ( disk_num * node_num ))
        output = "".join(lines)

    result["message"] = message
    result["output"] = output

    return result

@recordInfo(CMD_WRAPPER.format("drbdadm status all"), REC_FILE)
def checkDRBDRole(args=None):
    message = ""
    output = ""
    result = {"status":"fail", "message":"", "output":"", "skipall": False}

    cluster_env = args[0]

    #Own test steps
    primary_num = 0
    secondary_num = 0
    node_num = libDRBD.getNodesNumber(cluster_env)
    res_num = libDRBD.getResNumber(cluster_env)

    lines = os.popen("ssh root@%s drbdadm status all" % cluster_env["IP_NODE1"]).readlines()

    pa_p = re.compile("\srole:Primary")
    pa_s = re.compile("\srole:Secondary")
    for line in lines:
        if re.search(pa_p, line) is not None:
            primary_num += 1
            continue

        if re.search(pa_s, line) is not None:
            secondary_num += 1

    if primary_num == res_num and secondary_num == ( res_num * ( node_num -1 ) ):
        result["status"] = "pass"
    else:
        message = "Only %d in Primary and %d in Secondary." % (primary_num, secondary_num)
        output = "".join(lines)

    result["message"] = message
    result["output"] = output

    return result

@recordInfo(CMD_WRAPPER.format("blkid"), REC_FILE)
def checkMakeFS(args=None):
    message = ""
    output = ""
    result = {"status":"fail", "message":"", "output":"", "skipall": False}

    cluster_env = args[0]

    #Own test steps
    #"xfs" require 4096 blocks at least. by default /dev/drbd3 only 10M(2550 blocks)
    support_fs = ["ext4", "xfs", "ext3"]
    ok_list = []
    index = 0

    info = libDRBD.getDRBDInfo(cluster_env)

    if len(info) <= 0:
        result["status"] = "skip"
        return result

    for i in info:
        name = i["name"]
        pindex = i["primaries"][0][-1]
        device = i["device"]

        line = os.popen("ssh root@%s drbdadm dstate %s 2>/dev/null" %
                (cluster_env["IP_NODE%s" % pindex], name)).readline().strip()

        if line is not None and "UpToDate/UpToDate" in line:
            # Device /dev/drbd(i) found
            _ = os.popen("ssh root@%s mkfs.%s %s %s >/dev/null 2>&1" %
                         (cluster_env["IP_NODE%s" % pindex], support_fs[index],
                          ("-f" if support_fs[index] == "xfs" else ""), device)).readlines()
            print("Make file system on primary node of resource(%s)" % name)
            print("\tssh root@%s mkfs.%s %s %s >/dev/null 2>&1" %
                         (cluster_env["IP_NODE%s" % pindex], support_fs[index],
                          ("-f" if support_fs[index] == "xfs" else ""), device))

            #Since SLE-15-SP3-Full-x86_64-Build124.5, `lsblk -f` can't show FSTYPE correctly. (Likely BUG)
            #Use blkid instead, example:
            #  /dev/drbd0: UUID="dc3df020-d90e-486e-aacf-4034012e45a6" TYPE="ext4"
            #  /dev/drbd2: UUID="632aca5b-b5a8-4493-9226-72cce79aba83" TYPE="xfs"
            #  /dev/drbd3: UUID="4cd23219-bfd8-4d2b-8976-7f45b1ed2780" SEC_TYPE="ext2" TYPE="ext3"
            #command = "lsblk -f"
            command = "blkid"
            a = os.popen("ssh root@%s %s |grep %s" %
                         (cluster_env["IP_NODE%s" % pindex], command, os.path.basename(device))).readlines()

            flag = False
            for l in a:
                if support_fs[index] in l:
                    flag = True
                    ok_list.append(support_fs[index])

            if flag == False:
                message = "Fail to make filesystem %s on %s" % (support_fs[index], device)
                output = lines[0]
                break

            index = (index + 1) % len(support_fs)

    ok_output = " ".join(ok_list)

    if message == "" and output == "":
        result["status"] = "pass"

    result["message"] = message
    result["output"] = output

    return result

@recordInfo(CMD_WRAPPER.format("crm_mon -1r"), REC_FILE)
def checkPacemakerStatus(args=None):
    message = ""
    output = ""
    result = {"status":"fail", "message":"", "output":"", "skipall": False}

    cluster_env = args[0]

    #Own test steps
    resource_lists = []

    lines = os.popen("ssh root@%s crm configure show" % cluster_env["IP_NODE1"]).readlines()
    for line in lines:
        tmp = re.match("\s*params drbd_resource=([\w-]*)\s+.*", line)
        if tmp is not None:
            resource_lists.append(tmp.groups()[0])

    lines = os.popen("ssh root@%s crm_mon -1r" % cluster_env["IP_NODE1"]).readlines()

    for res in resource_lists:
        for i in range(len(lines)):
            if re.search("Master/Slave Set: ms_%s" % res, lines[i]) is not None:
                if re.search("Masters:\s*\[", lines[i+1]) is None:
                    message = "No Master of res ms_%s" % res
                    output = lines[i+1]
                    break

                if re.search("Slaves:\s*\[", lines[i+2]) is None:
                    message = "No Slaves of res ms_%s" % res
                    output = lines[i+2]
                    break

    if message == "" and output == "":
        result["status"] = "pass"

    result["message"] = message
    result["output"] = output

    return result

@recordInfo(CMD_WRAPPER.format("crm_mon -1r"), REC_FILE)
def switchDRBD(args=None):
    message = ""
    output = ""
    result = {"status":"fail", "message":"", "output":"", "skipall": False}

    cluster_env = args[0]
    info = libDRBD.getDRBDInfo(cluster_env)

    if len(info) <= 0:
        result["status"] = "skip"
        return result

    #Own test steps
    node_list = [ line.strip().split()[1] for line in os.popen("ssh root@%s crm_node -l" % cluster_env["IP_NODE1"]).readlines() ]

    # Find the resources configured in pacemaker. Not just via getDRBDInfo from drbdadm
    resource_lists = []
    lines = os.popen("ssh root@%s crm configure show" % cluster_env["IP_NODE1"]).readlines()
    for line in lines:
        tmp = re.match("\s*params drbd_resource=([\w-]*)\s+.*", line)
        if tmp is not None:
            resource_lists.append(tmp.groups()[0])

    # Move res
    mv_command = "ssh root@%s crm resource move ms_%s %s 2>&1"
    for res in resource_lists:
        for node in node_list:
            conflag = False

            for i in info:
                if i["name"] == res and node in i["primaries"]:
                    conflag = True
                    break

            # Unnecessary to move res if target node already in Primary
            if conflag:
                continue

            tmp = os.popen(mv_command % (cluster_env["IP_NODE1"], res, node)).readline()
            # Example:
            # Succeed: INFO: Move constraint created for ms_1-multi-0 to Leap42_2-test-node1\n
            # Fail: Error performing operation: ms_1-multi-0 is already active on Leap42_2-test-node2\n
            if "is already active on" in tmp or "Situation already as requested" in tmp \
                or "Already in requested state" in tmp or "Requested item already exists" in tmp:
                # Already master, try the next node
                # Should not entry here! Since will continue when node not in Primary role.
                continue
            elif  "Move constraint created" in tmp:
                # Succeed on moving resource, change next resource
                break
            else:
                # Fail to move resource
                message = "Fail to move res: %s to node: %s." % (res, node)
                output = tmp

    # Sleep 30 secs for moving resources
    sleep(60)

    if message == "" and output == "":
        result["status"] = "pass"

    result["message"] = message
    result["output"] = output

    return result


def Run(conf, xmldir):
    cluster_env = readClusterConf(conf)

    testcases = []
    #Name of Test Suite
    TestSuiteName = "Setup HA Cluster"
    #Name of junit xml file
    JunitXML = "junit-drbd-pacemaker.xml"

    #Define testcases
    #testcases = [(TestcaseName, TestcaseClass, TestcaseFunction)]
    #eg.
    # ('PacemakerService', 'SetupCluster.service', runPackmakerService)
    #Define function runPackmakerService before using
    cases_def = [('drbdPacemakerRes', 'SetupCluster.drbd', configurePacemaker),
                 ('drbdCheckVersion', 'SetupCluster.drbd', checkDRBDVersion),
                 ('drbdUpToDateBefore', 'DRBD.disks', checkDRBDState),
                 ('drbdPrimaryBefore', 'DRBD.state', checkDRBDRole),
                 ('drbdShowInPacemaker', 'DRBD.pacemaker', checkPacemakerStatus),
                 ('drbdMakeFS', 'DRBD.fs', checkMakeFS),
                 ('drbdSwitchMaster', 'DRBD.pacemaker', switchDRBD),
                 ('drbdUpToDateAfter', 'DRBD.disks', checkDRBDState),
                 ('drbdPrimaryAfter', 'DRBD.state', checkDRBDRole),
                 ('drbdShowInPacemakerAfter', 'DRBD.pacemaker', checkPacemakerStatus)]
                 #('ConfigureRes', 'SetupCluster.resources', runConfigureRes)]

    #Not necessary to modify the lines below!
    skip_flag = False
    for a_case in cases_def:
        case = TestCase(a_case[0], a_case[1])
        testcases.append(case)
        if skip_flag:
            skipCase(case, "Can not test!",
                     "Pacemaker service of the first node not started or didn't configure DRBD.")
            continue
        print("Running test case %s:%s()..." % (__file__, a_case[0]))
        skip_flag = assertCase(case, a_case[2], cluster_env)
        sleep(3)

    ts = TestSuite(TestSuiteName, testcases)

    with open(xmldir+"/"+JunitXML, "w") as f:
        ts.to_file(f, [ts])

if __name__ == "__main__":
    Run(sys.argv[1], sys.argv[2])
