#########################################################################
# File Name: monitor-build-change.sh
# Author: ZhiLong Liu
# mail: zlliu@suse.com
#########################################################################
#!/bin/bash

# Because SLP system would download and
# unzip HA image before download server
# milestone image, thus just monitor the
# server image build number is enough.
PRODUCT=Server
#PRODUCT=HA
VERSION=12
PATCHLEVEL=0
ARCH=x86_64

if [ ${PATCHLEVEL} != 0 ]
then
    PATCHLEVEL=SP${PATCHLEVEL}-
else
    PATCHLEVEL=""
fi

PATTERN="SLE-${PRODUCT}-${VERSION}-${PATCHLEVEL}${ARCH}-Build"
SLP_URL="http://147.2.207.1/dist/install/SLP"
KERNEL_MILESTONE="SLE-${VERSION}-${PATCHLEVEL}${PRODUCT}-LATEST"
MEDIA="${ARCH}/CD1/media.1"
O_K_FILE="sle_build"
N_K_FILE="sle_newbuild"

die()
{
    echo -e "\n\tERROR: $* \n"
    exit 3
}

download_file()
{
    wget -c $SLP_URL/$KERNEL_MILESTONE/$MEDIA/build -O $N_K_FILE &> /dev/null
    [ $? -eq 0 ] ||
        die "download $N_K_FILE failed."
}

main()
{
    download_file
    [ ! -e $O_K_FILE ] && cp -f $N_K_FILE $O_K_FILE && echo "First run." && exit 0

    O_K_NUM=$(cat $O_K_FILE|sed "s/${PATTERN}//")
    N_K_NUM=$(cat $N_K_FILE|sed "s/${PATTERN}//")
    echo "Old build is $O_K_NUM, new build is $N_K_NUM."

    if [ -z "$O_K_NUM" -o -z "$N_K_NUM" -o "$O_K_NUM" -gt "$N_K_NUM" ]
    then
        die "No kernel build number found or the pattern changed."
    elif [ $O_K_NUM -eq $N_K_NUM ]
    then
        echo "Build number didn't change. Do nothing."
    else
        # [ $O_K_NUM -lt $N_K_NUM ]
        echo "New image Build number has changed."
        cp -f $N_K_FILE $O_K_FILE
        rm -fr $N_K_FILE
        exit 0
    fi

    rm -fr $N_K_FILE
}

main

exit 2
