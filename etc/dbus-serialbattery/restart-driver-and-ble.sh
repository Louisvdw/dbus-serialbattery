#!/bin/bash

# remove comment for easier troubleshooting
#set -x

sh /data/etc/dbus-serialbattery/reinstalllocal.sh

sh /data/etc/dbus-serialbattery/restartservice.sh

/etc/init.d/bluetooth restart
