#!/usr/bin/python3

import os
import pprint

import shell

def command(cmd, log=False):
    sh = shell.shell(cmd)
    ret = sh.output()

    if log:
        print("Called cmd: %s" % cmd)
        print("Return code: %s" % sh.code)

    return ret

def mount_iso(src, mount_dir, create_dir=False):
    if not os.path.exists(src):
        return False

    if not os.path.exists(mount_dir):
        if create_dir:
            os.makedirs(mount_dir)
        else:
            return False

    # Full string:
    #   mount: /mnt/testdummy/folder1: WARNING: device write-protected, mounted read-only.
    string = "WARNING: device write-protected, mounted read-only."

    #mount won't write to stdout, instead write to stderr...
    sh = shell.shell("mount -o loop {src} {mdir}".format(src=src, mdir=mount_dir))
    if string not in sh.errors()[0]:
        return False

    return True

def umount_iso(src):
    if not os.path.exists(src):
        return False

    fname = os.path.basename(src)
    sh = shell.shell("mount |grep {fname}".format(fname=fname))
    if sh.code:
        #Not mount
        return True

    shell.shell("umount {src}".format(src=src))

    return True

def test():
    pprint.pprint(command("ls -lh", True))

    mount_iso("/home/nwang/Images/SLES/SLE-12-SP3-HA-DVD-x86_64-GM-CD1.iso", "/mnt/testdummy/folder1")
    ##pprint.pprint(command("mount", True))
    umount_iso("/home/nwang/Images/SLES/SLE-12-SP3-HA-DVD-x86_64-GM-CD1.iso")

if __name__ == "__main__":
    test()
