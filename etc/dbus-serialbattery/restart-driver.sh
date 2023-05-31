#!/bin/bash

# remove comment for easier troubleshooting
#set -x

# copy config.ini in case it was changed
cp -f /data/etc/dbus-serialbattery/config.ini /opt/victronenergy/dbus-serialbattery/config.ini

# would not restart ble services
# svc -d -u /service/dbus-serialbattery

# kill driver, if running. It gets restarted by the service daemon
pkill -f "python .*/dbus-serialbattery.py"


# get BMS list from config file
bluetooth_bms=$(awk -F "=" '/^BLUETOOTH_BMS/ {print $2}' /data/etc/dbus-serialbattery/config.ini)
# clear whitespaces
bluetooth_bms_clean="$(echo $bluetooth_bms | sed 's/\s*,\s*/,/g')"
# split into array
IFS="," read -r -a bms_array <<< "$bluetooth_bms_clean"
length=${#bms_array[@]}

# restart bluetooth service, if Bluetooth BMS configured
if [ $length -gt 0 ]; then
    /etc/init.d/bluetooth restart
fi
