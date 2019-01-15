#!/bin/bash

# Because SLP system would download and
# unzip HA image before download server
# milestone image, thus just monitor the
# server image build number is enough.
PRODUCT=Installer
#PRODUCT=HA
VERSION=15
PATCHLEVEL=1
ARCH=x86_64

SLP_URL="http://mirror.suse.asia/dist/install/SLP/"
DIR="/tmp/jenkins-dummy/build-change/"

if [ ${PATCHLEVEL} != 0 ]
then
    PATCHLEVEL=SP${PATCHLEVEL}-
else
    PATCHLEVEL=""
fi

die()
{
    echo -e "\n\tERROR: $* \n"
    exit 3
}

download_file()
{
    #wget won't redownload if N_K_FILE exist
    #The file is already fully retrieved; nothing to do.
    rm -rf $N_K_FILE

    wget $SLP_URL/$KERNEL_MILESTONE/$MEDIA/media -O $N_K_FILE &> /dev/null
    [ $? -eq 0 ] ||
        die "download $N_K_FILE failed."
    sle15_adapt $N_K_FILE
}

sle15_adapt()
{
    cat ${1} | grep Build | sed "/SUSE - /d" > ${1}.tmp
    mv ${1}.tmp ${1}
}

main()
{
    [ -d ${DIR} ] || rm -rf ${DIR} && mkdir -p ${DIR}

    download_file
    [ ! -e $O_K_FILE ] && cp -f $N_K_FILE $O_K_FILE && echo "First run." && exit 0

    # Delete "." when build no is xxx.y
    O_K_NUM=$(cat $O_K_FILE|sed "s/${PATTERN}//"|tr -d ".")
    N_K_NUM=$(cat $N_K_FILE|sed "s/${PATTERN}//"|tr -d ".")
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

while getopts "u:v:P:a:D:h" OPT; do
    case $OPT in
        u)
            SLP_URL="$OPTARG";;
        v)
            VERSION="$OPTARG";;
        P)
            PATCHLEVEL="$OPTARG";;
        a)
            ARCH="$OPTARG";;
        D)
            DIR=${DIR}"$OPTARG";;
        h)
            echo "monitor-build-change.sh [-u SLP_URL] [-v VERSION] [-P PATCHLEVEL] [-a arch] [-D dir]"
            exit 0;;
    esac
done

PATTERN="SLE-${VERSION}-${PATCHLEVEL}${PRODUCT}-DVD-${ARCH}-Build"
KERNEL_MILESTONE="SLE-${VERSION}-${PATCHLEVEL}${PRODUCT}-LATEST"
MEDIA="${ARCH}/CD1/media.1"
O_K_FILE="${DIR}/sle_build"
N_K_FILE="${DIR}/sle_newbuild"

main

exit 2
