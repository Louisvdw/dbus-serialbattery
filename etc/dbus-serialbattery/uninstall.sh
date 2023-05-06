#!/bin/bash

# remove comment for easier troubleshooting
#set -x

# handle read only mounts
sh /opt/victronenergy/swupdate-scripts/remount-rw.sh

# remove files, don't use variables here, since on an error the whole /opt/victronenergy gets deleted
rm -f /data/conf/serial-starter.d/dbus-serialbattery.conf
rm -rf /opt/victronenergy/service/dbus-serialbattery
rm -rf /opt/victronenergy/service-templates/dbus-serialbattery
rm -rf /opt/victronenergy/dbus-serialbattery

# kill if running
pkill -f "python .*/dbus-serialbattery.py"

# remove install-script from rc.local
sed -i "/sh \/data\/etc\/dbus-serialbattery\/reinstall-local.sh/d" /data/rc.local


### needed for upgrading from older versions | start ###
# remove old install script from rc.local
sed -i "/sh \/data\/etc\/$DRIVERNAME\/reinstalllocal.sh/d" /data/rc.local
### needed for upgrading from older versions | end ###
