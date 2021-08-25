#!/usr/bin/python3

import sys, os, re

def getDRBDInfo(cluster_env):
    lines = os.popen("ssh root@%s drbdadm dump all" % cluster_env["IP_NODE1"]).readlines()
    resources = [ line.strip().split()[1] for line in lines if line.startswith("resource ") ]

    info = []

    for r in resources:
        res = {}
        res["name"] = r
        res["device"] = os.popen("ssh root@%s drbdadm sh-dev %s" % (cluster_env["IP_NODE1"], r)).readline().strip()
        res["primaries"] = []

        lines = os.popen("ssh root@%s drbdadm status %s" % (cluster_env["IP_NODE1"], r)).readlines()
        # example:
        # 1-single-0 role:Primary
        #   disk:UpToDate
        #   nick-SLE15-SP3-drbd-milestone-node2 role:Secondary
        #     peer-disk:UpToDate
        #   nick-SLE15-SP3-drbd-milestone-node3 role:Secondary
        #     peer-disk:UpToDate
        # 
        # 1-single-1 role:Secondary
        #   disk:UpToDate
        #   nick-SLE15-SP3-drbd-milestone-node2 role:Primary
        #     peer-disk:UpToDate
        #   nick-SLE15-SP3-drbd-milestone-node3 role:Secondary
        #     peer-disk:UpToDate

        for line in lines:
            if " role:Primary" in line:
                if line.startswith(" "):
                    res["primaries"].append(line.strip().split()[0])
                else:
                    res["primaries"].append(cluster_env["HOSTNAME_NODE1"])

        info.append(res)

    return info

def getNodesNumber(cluster_env):
    lines = os.popen("ssh root@%s crm_node -l" % cluster_env["IP_NODE1"]).readlines()
    return len(lines)

def getResNumber(cluster_env):
    ''' Get the resource numbers per node. '''
    resource_lists = []

    lines = os.popen("ssh root@%s crm configure show" % cluster_env["IP_NODE1"]).readlines()
    for line in lines:
        tmp = re.match("\s*params drbd_resource=([\w-]*)\s+.*", line)
        if tmp is not None:
            resource_lists.append(tmp.groups()[0])
    return len(resource_lists)

def getVolumeNumber(cluster_env):
    ''' Get the volume numbers per node. '''
    lines = os.popen("ssh root@%s drbdadm dstate all" % cluster_env["IP_NODE1"]).readlines()
    return len(lines)
