#!/bin/bash

# executed before archive extraction on USB install
# see https://github.com/victronenergy/meta-victronenergy/blob/15fa33c3e5430f7c08a688dc02171f5be9a81c84/meta-venus/recipes-core/initscripts/files/update-data.sh#L42


# backup config.ini
if [ -f "/data/etc/dbus-serialbattery/config.ini" ]; then
    mv /data/etc/dbus-serialbattery/config.ini /data/etc/dbus-serialbattery_config.ini.backup
fi

# remove old driver
if [ -f "/data/etc/dbus-serialbattery" ]; then
    rm -rf /data/etc/dbus-serialbattery
fi
