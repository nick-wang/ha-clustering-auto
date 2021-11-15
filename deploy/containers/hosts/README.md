HA container:
    Use Ctrl + p -> Ctrl + q to detect instead of exit
    Use /data/start.sh to start services.

1. CI(jenkins) services: container:8080 -> host:8080
        rcjenkins start/stop
2. http services: container:80 -> host:8090
        apachectl start/stop
