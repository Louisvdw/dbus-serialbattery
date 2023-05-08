#!/bin/bash

# remove comment for easier troubleshooting
#set -x

# handle read only mounts
sh /opt/victronenergy/swupdate-scripts/remount-rw.sh

# remove files, don't use variables here, since on an error the whole /opt/victronenergy gets deleted
rm -f /data/conf/serial-starter.d/dbus-serialbattery.conf
rm -rf /service/dbus-serialbattery.*
rm -rf /service/dbus-blebattery.*

# remove install script from rc.local
sed -i "/sh \/data\/etc\/dbus-serialbattery\/reinstall-local.sh/d" /data/rc.local


### needed for upgrading from older versions | start ###
# remove old drivers before changing from dbus-blebattery-$1 to dbus-blebattery.$1
rm -rf /service/dbus-blebattery-*
# remove old install script from rc.local
sed -i "/sh \/data\/etc\/dbus-serialbattery\/reinstalllocal.sh/d" /data/rc.local
# remove old entry from rc.local
sed -i "/sh \/data\/etc\/dbus-serialbattery\/installble.sh/d" /data/rc.local
### needed for upgrading from older versions | end ###


# kill serial starter, to reload changes
pkill -f "/opt/victronenergy/serial-starter/serial-starter.sh"

# kill driver, if running
pkill -f "serialbattery"
pkill -f "blebattery"
