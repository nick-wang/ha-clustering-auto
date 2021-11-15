#!/bin/bash

Docker_image="nickwang/jenkins-ci-host"
NAME="jenkins-ci-host"

CI_HOST="ci.ha.suse.asia" # dns ci.ha.suse.asia -> 10.67.160.200
# ADD_IP depends on data/getHost.sh
eval $(grep "ADD_IP=" data/getHost.sh)

# How about prepare a ENV file into $(pwd)/data
# Including local IP address, etc
function create_container()
{
    sh ./data/getHost.sh

    # Exposed jenkins server on host port 8080 in images
	# --restart:  no, on-failure:10, always
    # Will create a http server on host port 8090. Use 80?
    # -v /lib/modules:/lib/modules  \ for configfs kernel module with targetcli/iscsi
	# -v /dev:/dev \ for mount loop device or TW iso. Error: failed to setup loop device for ...
    echo "Create docker container: ${NAME}"
    docker run -it -d --name=${NAME} --hostname ${NAME} \
           --privileged \
           --restart=always \
           -p 8080:8080 \
           -p 8090:80 \
           -v "$(pwd)/data:/data" \
           -v "/dev:/dev" \
           ${Docker_image} /bin/bash
}

function start_container()
{
    echo "Start docker container: ${NAME}"
    docker start ${NAME}
}

function start_services()
{
    echo -e "Starting services if not started..."
    #docker exec -t ${NAME} /bin/sh -c "/data/start.sh"
    docker exec -t ${NAME} /bin/sh -c "apachectl start 2>/dev/null; rcjenkins start"

    echo -e "\tjenkins service -> localhost:8080\n\thttp service -> localhost:8090\n"
}

function add_ip_on_host()
{
	if [ x"${ADD_IP}" != x"true" ]; then
		return
	fi

	echo -e "Prepare to add IP address of ${CI_HOST} if not able to ping"
    # Since ci.ha.suse.asia bind to 10.67.160.200
	# Add ip address to br0/br1 when not existed
	ping -c 1 -w 5 ${CI_HOST} >/dev/null
    if [ $? -ne 0 ]; then
	    IP1=$(nslookup ${CI_HOST}|grep "Address:"|grep "10.67.160"|cut -d " " -f 2)
		IP2=$(echo $IP1|awk -F "." '{print $1"."$2"."$3+1"."$4}')

		# Remove via ip addr del 10.67.160.200/21 dev br0
		#            ip addr del 10.67.161.200/21 dev br1
        ip addr add ${IP1}/21 dev br0
		ip addr add ${IP2}/21 dev br1

        ip addr |grep "${IP1}/21" >/dev/null
        if [ $? -eq 0 ]; then
	        echo "IP address ${IP1} available on host."
	    fi

        ip addr |grep "${IP2}/21" >/dev/null
        if [ $? -eq 0 ]; then
	        echo "IP address ${IP2} available on host."
	    fi
	else
		echo "${CI_HOST} has already accessible."
	fi

}

docker container inspect ${NAME} >/dev/null 2>&1
if [ $? -ne 0 ]; then
    create_container
else
	docker container inspect ${NAME} |grep '"Status": '|grep 'exited' >/dev/null
    if [ $? -eq 0 ]; then
        start_container
	else
		state=$(docker container inspect ${NAME} |grep '"Status": '|cut -d ":" -f 2|tr -d ",")
        echo "docker container ${NAME} is in${state} already"
    fi
fi

add_ip_on_host
start_services
