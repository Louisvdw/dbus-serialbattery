#!/bin/sh
set -x
opkg update
opkg install python3-misc python3-pip
pip3 install bleak
tar -zxf ./venus-data.tar.gz -C /data
sh /data/etc/dbus-serialbattery/reinstalllocal.sh
echo "make sure to disable Settings/Bluetooth in the Remote-Console to prevent reconnects every minute. In case of crash after ~12-16 hours disable raspberry pi 3 internal bluetooth via dtoverlay and use an external usb bluetooth-dongle"

