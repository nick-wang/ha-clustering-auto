#########################################################################
# File Name: monitor-build-change.sh
# Author: ZhiLong Liu
# mail: zlliu@suse.com
#########################################################################
#!/bin/bash

SLP_URL="http://147.2.207.1/dist/install/SLP"
KERNEL_MILESTONE="SLE-12-SP2-Server-LATEST"
MEDIA="x86_64/CD1/media.1"
O_K_FILE="kernel_build"
N_K_FILE="kernel_newbuild"

# Because SLP system would download and
# unzip HA image before download server
# milestone image, thus just monitor the
# server image build number is enough.

#HA_MILESTONE="SLE-12-SP2-HA-LATEST"
#O_H_FILE="ha_build"
#N_H_FILE="ha_newbuild"

die()
{
	echo -e "\n\tERROR: $* \n"
	exit 3
}

download_file()
{
	[ -f $O_K_FILE ] || {
		wget -c $SLP_URL/$KERNEL_MILESTONE/$MEDIA/build -O $O_K_FILE &> /dev/null
		[ $? -eq 0 ] ||
			die "download $O_K_FILE failed."
	} 

	wget -c $SLP_URL/$KERNEL_MILESTONE/$MEDIA/build -O $N_K_FILE &> /dev/null
	[ $? -eq 0 ] ||
		die "download $N_K_FILE failed."
}

main()
{
	[ -s $O_K_FILE ] ||
		rm -fr $O_K_FILE
	rm -fr $N_K_FILE

	download_file
	O_K_NUM=$(grep -oP "Build[0-9]+" $O_K_FILE)
	N_K_NUM=$(grep -oP "Build[0-9]+" $N_K_FILE)

	if [ -z "$O_K_NUM" -o -z "$N_K_NUM" ]
	then
		die "No kernel build number found."
	elif [ $O_K_NUM != $N_K_NUM ]
	then
		echo "New image Build number has changed."
		cp -f $N_K_FILE $O_K_FILE
		exit 0
	else
		rm -fr $N_K_FILE
	fi
}

main

exit 2
