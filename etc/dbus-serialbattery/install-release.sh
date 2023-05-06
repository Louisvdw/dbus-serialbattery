#!/bin/bash

# remove comment for easier troubleshooting
#set -x

# download latest release
curl -s https://api.github.com/repos/Louisvdw/dbus-serialbattery/releases/latest | grep "browser_download_url.*gz" | cut -d : -f 2,3 | tr -d \" | wget -O venus-data.tar.gz -qi -
# extract the latest install-local script to run
tar -zxf ./venus-data.tar.gz -C /data etc/dbus-serialbattery/install-local.sh

# extract and install driver
sh /data/etc/dbus-serialbattery/install-local.sh
