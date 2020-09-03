#!/bin/bash
#
# Start script for dbus-serialbattery
#	First parameter: tty device to use
#
# Keep this script running with daemon tools. If it exits because the
# connection crashes, or whatever, daemon tools will start a new one.
#

. /opt/victronenergy/serial-starter/run-service.sh

exec /opt/victronenergy/dbus-serialbattery/dbus-serialbattery.py /dev/$tty
