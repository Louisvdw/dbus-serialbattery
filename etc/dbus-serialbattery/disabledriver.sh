#!/bin/bash

# remove comment for easier troubleshooting
#set -x

DRIVERNAME=dbus-serialbattery

# handle read only mounts
sh /opt/victronenergy/swupdate-scripts/remount-rw.sh

# remove files
rm -f /data/conf/serial-starter.d
rm -rf /service/dbus-blebattery-*

# kill if running
pkill -f "python .*/$DRIVERNAME.py"

# remove install-script from rc.local
sed -i "/sh \/data\/etc\/$DRIVERNAME\/reinstalllocal.sh/d" /data/rc.local
sed -i "/sh \/data\/etc\/$DRIVERNAME\/installble.sh/d" /data/rc.local
