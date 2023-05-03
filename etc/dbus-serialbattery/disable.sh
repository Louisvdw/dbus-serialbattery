#!/bin/bash

# remove comment for easier troubleshooting
#set -x

DRIVERNAME=dbus-serialbattery

# handle read only mounts
sh /opt/victronenergy/swupdate-scripts/remount-rw.sh

# remove files
rm -f /data/conf/serial-starter.d/$DRIVERNAME.conf
rm -rf /service/dbus-blebattery.*

# kill driver, if running. It gets restarted by the service daemon
pkill -f "python .*/$DRIVERNAME.py"

# remove install script from rc.local
sed -i "/sh \/data\/etc\/$DRIVERNAME\/reinstall-local.sh/d" /data/rc.local


### needed for upgrading from older versions | start ###
# remove old drivers before changing from dbus-blebattery-$1 to dbus-blebattery.$1
rm -rf /service/dbus-blebattery-*
# remove old install script from rc.local
sed -i "/sh \/data\/etc\/$DRIVERNAME\/reinstalllocal.sh/d" /data/rc.local
# remove old entry from rc.local
sed -i "/sh \/data\/etc\/dbus-serialbattery\/installble.sh/d" /data/rc.local
### needed for upgrading from older versions | end ###
