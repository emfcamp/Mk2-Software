#!/bin/bash

### BEGIN INIT INFO
# Provides:          tilda-gateway-supervisor
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Download, run and restart tilda gateway script after excsueption
### END INIT INFO

# This is the script that gets started after startup. Only this script
# is needed, nothing else.
# Make sure that user "tilda" exists! (useradd tilda) and a folder "/tilda" and "/var/log/tilda"
# that is owned by tilda. All this can be done by running "setup" on this scipt
# Copy this script in /etc/init.d/tilda-gateway-supervisor, chmod 755 and execute
# "sudo update-rc.d tilda-gateway-supervisor defaults" to make it run after boot

pushd `dirname $0` > /dev/null
SCRIPTPATH=`pwd`
popd > /dev/null

prgcmd="$SCRIPTPATH/$(basename $0) worker" # What gets executed?
prgname=tildagws # What's the name (used to ensure only one instance is running)
prguser=root # Will be dropped down when the actual script is started
pidfile=/var/run/tilda-gateway-supervisor.pid # Where should the pid file be stored?

worker() {
    while :
    do
        cd /tilda

        echo "Downloading current version of software from github..."
        cd Mk2-Software
        git pull --rebase

        echo "Run setup..."
        ./setup.py develop

        echo "Run gateway..."
        sudo -u tilda ./bin/gateway.py

        echo "Process died, start again in 5 sec"
        sleep 5
    done
}

setup() {
    useradd tilda
    usermod -a -G dialout tilda
    mkdir /tilda
    cd /tilda
    git clone https://github.com/emfcamp/Mk2-Software.git
    mkdir /var/log/tilda
    chown tilda /tilda
    chown tilda /var/log/tilda
}

start() {
    if [ -f $pidfile ]; then
        pid=`cat $pidfile`
        kill -0 $pid >& /dev/null
        if [ $? -eq 0 ]; then
            echo "Service has already been started."
            return 1
        fi
    fi

    nohup start-stop-daemon -c $prguser -n $prgname -p $pidfile -m --exec /usr/bin/env --start $prgcmd >>/var/log/tilda/gateway.log 2>&1 &

    if [ $? -eq 0 ]; then
        echo "Service started."
        return 0
    else
        echo "Failed to start service."
        return 1
    fi
}

stop() {

    if [ ! -f $pidfile ]; then
        echo "Service not started."
        return 1
    fi

    start-stop-daemon -p $pidfile --stop
    if [ $? -ne 0 ]; then
        echo "Failed to stop service."
        return 1
    fi

    echo -e "\nService stopped."
    rm $pidfile
}

status() {

    if [ -f $pidfile ]; then
        pid=`cat $pidfile`
        kill -0 $pid >& /dev/null
        if [ $? -eq 0 ]; then
            echo "Service running. (PID: ${pid})"
            return 0
        else
            echo "Service might have crashed. (PID: ${pid} file remains)"
            return 1
        fi
    else
        echo "Service not started."
        return 0
    fi
}

restart() {
    stop
    if [ $? -ne 0 ]; then
        return 1
    fi

    sleep 2

    start
    return $?
}

case "$1" in
    start | stop | status | restart | worker | setup)
        $1
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart|worker|setup}"
        exit 2
esac
exit 0

