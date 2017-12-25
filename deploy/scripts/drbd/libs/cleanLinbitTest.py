#!/usr/bin/env python2

import os, subprocess
import time

vg_name = "scratch"

def remove_lvm():
    lvs = [ line.strip() for line in
        os.popen('lvs |grep %s' % vg_name) ]

    for lv in lvs:
        lv_name = lv.split()[0]
        os.popen("lvremove -f /dev/scratch/%s" % lv_name)

def check_res_exist(show=False):
    res = [ line.strip() for line in
        os.popen('drbdsetup status |grep "^\w" |cut -d " " -f 1').readlines() ]

    if len(res) != 0:
        if show == True:
            print "Resource existed!!!"
            print "Get the resource name: %s" % res
    else:
        if show == True:
            print "No resource defined."
            print "Remove lvs of scratch."
        return None

    # If multiple res exist, previous test case is not clean
    return res

def show_status():
    # subprocess.call will show output to screen
    # subprocess.check_output will show nothing
    tmp = subprocess.call( [ "drbdsetup", "status" ] )

def down_res(res):
    tmp_num = os.popen( "drbdsetup show %s |grep -c connection" %
        res ).readline().strip()
    node_num = int(tmp_num) + 1

    # id:0 including the node itself, error msg will show when delete itself
    # error msg: " additional info from kernel: "
    #            " peer node id cannot be my own node id "
    for peer_id in range(0, node_num):
        os.popen( "drbdsetup del-peer %s %d >/dev/null 2>&1"
                  % (res, peer_id) )

    time.sleep(2)
    subprocess.call( [ "drbdsetup", "down", res ] )

def main():
    res=check_res_exist()

    #show_status()
    if res is not None:
        for resource in res:
            down_res(resource)
    #show_status()

    remove_lvm()

if __name__ == "__main__":
    main()
