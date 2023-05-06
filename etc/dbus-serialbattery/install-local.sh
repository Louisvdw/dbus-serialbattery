#!/bin/sh

# remove comment for easier troubleshooting
#set -x

# backup config.ini
if [ -f "/data/etc/dbus-serialbattery/config.ini" ]; then
    mv /data/etc/dbus-serialbattery/config.ini /data/etc/config.ini
fi

# remove old driver
rm -rf /data/etc/dbus-serialbattery

# extract driver
tar -zxf ./venus-data.tar.gz -C /data

# restore config.ini
if [ -f "/data/etc/config.ini" ]; then
    mv /data/etc/config.ini /data/etc/dbus-serialbattery/config.ini
fi

# install driver
sh /data/etc/dbus-serialbattery/reinstall-local.sh
