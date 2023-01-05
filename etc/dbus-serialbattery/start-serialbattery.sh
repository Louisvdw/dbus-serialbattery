#!/bin/bash
#

. /opt/victronenergy/serial-starter/run-service.sh

# app=$(dirname $0)/dbus-serialbattery.py

# start -x -s $tty
app="python /opt/victronenergy/dbus-serialbattery/dbus-serialbattery.py"
args="/dev/$tty"
start $args
