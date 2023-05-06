#!/bin/bash

# remove comment for easier troubleshooting
#set -x

DRIVERNAME=dbus-serialbattery

# handle read only mounts
sh /opt/victronenergy/swupdate-scripts/remount-rw.sh

# remove files
rm -f /data/conf/serial-starter.d/$DRIVERNAME.conf

# kill driver, if running. It gets restarted by the service daemon
pkill -f "python .*/$DRIVERNAME.py"

# remove install script from rc.local
sed -i "/sh \/data\/etc\/$DRIVERNAME\/reinstall-local.sh/d" /data/rc.local


### needed for upgrading from older versions | start ###
# remove old install script from rc.local
sed -i "/sh \/data\/etc\/$DRIVERNAME\/reinstalllocal.sh/d" /data/rc.local
### needed for upgrading from older versions | end ###
