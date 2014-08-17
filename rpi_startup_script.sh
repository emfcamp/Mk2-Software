#!/bin/bash

### BEGIN INIT INFO
# Provides:          tilda-gateway-supervisor
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Download, run and restart tilda gateway script after exception
# Description:       Download, run and restart tilda gateway script after exception
### END INIT INFO

# This is the script that gets started after startup. Only this script
# is needed, nothing else. Make sure that user "tilda" exists! (useradd tilda)
# Copy this script in /etc/init.d/tilda-gateway-supervisor, chmod 755 and execute
# "sudo update-rc.d tilda-gateway-supervisor defaults" to make it run after boot

software_root="/tildamk2Software"

prgcmd="$(basename $0) worker" # What gets executed?
prgname=tilda-gateway-supervisor # What's the name (used to ensure only one instance is running)
prguser=tilda # Which user should be used
pidfile=/var/run/tilda-gateway-supervisor.pid # Where should the pid file be stored?

# If you want a command to always run, put it here

# Carry out specific functions when asked to by the system
case "$1" in
    start)
        echo "Starting tilda-gateway-supervisor"
        # run application you want to start
        /etc/init.d/tilda-gateway-supervisor worker
        ;;
    stop)
        echo "Stopping tilda-gateway-supervisor"
        # kill application you want to stop
        killall tilda-gateway-supervisor
        ;;
    worker)
        while :
        do
            echo "Press [CTRL+C] to stop.."
            sleep 1
        done

    *)
        echo "Usage: sudo service tilda-gateway-supervisor {start|stop}"
        exit 1
        ;;
esac

exit 0