#!/bin/bash

cd /var/lib/clustermd-autotest
sleep 1
rm -fr /root/tt
./test --testdir=clustermd_tests --save-logs --logdir=/root/tt --keep-going

cd /root/
tar czvf test_result.tar.gz /root/tt/*

exit 0
