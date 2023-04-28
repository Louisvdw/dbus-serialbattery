#!/bin/bash

# remove comment for easier troubleshooting
#set -x

DRIVERNAME=dbus-serialbattery

# handle read only mounts
sh /opt/victronenergy/swupdate-scripts/remount-rw.sh

# remove files
rm -f /data/conf/serial-starter.d/$DRIVERNAME.conf
rm -rf /service/dbus-blebattery.*

# remove old drivers before changing from dbus-blebattery-$1 to dbus-blebattery.$1
# can be removed on second release (>1.0.0)
rm -rf /service/dbus-blebattery-*

# kill if running
pkill -f "python .*/$DRIVERNAME.py"

# remove install-script from rc.local
sed -i "/sh \/data\/etc\/$DRIVERNAME\/reinstalllocal.sh/d" /data/rc.local
sed -i "/sh \/data\/etc\/$DRIVERNAME\/installble.sh/d" /data/rc.local
