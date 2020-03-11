# Known issue1:
> Fail to get the backing image info When virtual machine is running.
> Due to get "write" lock error.
>
bj-ha-2:/tmp/jenkins-work/ha-share/cleanVM # virsh domblklist  SLE15-sp2-drbd-obstest-node3
 Target   Source
------------------------------------------------------------------------
 vda      /mnt/vm/sles_nick/SUSE-HA-SLE15-sp2-drbd-obstest-node3.qcow2
 vdb      /mnt/vm/sles_nick/SLE15-sp2-drbd-obstest-node3-disk1.raw
 vdc      /mnt/vm/sles_nick/SLE15-sp2-drbd-obstest-node3-disk2.raw

bj-ha-2:/tmp/jenkins-work/ha-share/cleanVM # qemu-img info /mnt/vm/sles_nick/SUSE-HA-SLE15-sp2-drbd-obstest-node3.qcow2
qemu-img: Could not open '/mnt/vm/sles_nick/SUSE-HA-SLE15-sp2-drbd-obstest-node3.qcow2': Failed to get shared "write" lock
Is another process using the image [/mnt/vm/sles_nick/SUSE-HA-SLE15-sp2-drbd-obstest-node3.qcow2]?

bj-ha-2:/tmp/jenkins-work/ha-share/cleanVM # virsh destroy SLE15-sp2-drbd-obstest-node3
Domain SLE15-sp2-drbd-obstest-node3 destroyed

bj-ha-2:/tmp/jenkins-work/ha-share/cleanVM # qemu-img info /mnt/vm/sles_nick/SUSE-HA-SLE15-sp2-drbd-obstest-node3.qcow2
image: /mnt/vm/sles_nick/SUSE-HA-SLE15-sp2-drbd-obstest-node3.qcow2
file format: qcow2
virtual size: 15G (16106127360 bytes)
disk size: 816M
cluster_size: 65536
backing file: /mnt/vm/sle_base/SUSE-HA-Full-15-SP2-x86_64-Build150.3-size15360-base.qcow2
Format specific information:
    compat: 1.1
    lazy refcounts: false
    refcount bits: 16
    corrupt: false

