#!/bin/sh

# remove comment for easier troubleshooting
#set -x

# extract driver
tar -zxf ./venus-data.tar.gz -C /data

# install driver
sh /data/etc/dbus-serialbattery/reinstalllocal.sh
