#########################################################################
# File Name: test.sh
# Author: bin liu
# mail: bliu@suse.com
# Created Time: Tue 15 Sep 2015 10:05:57 AM CST
#########################################################################
#!/bin/bash

node_list=$1
node=$2

OLD_IFS="$IFS"
IFS=","

arr=($node_list)
IFS="$OLD_IFS"
str=' '
for s in ${arr[@]}
do
	if [ $s == $node ];then
		continue
	fi
	if [ "$str" == ' ' ];then
		str=$s
	else
        str="$str,$s"
	fi
done
echo $str
