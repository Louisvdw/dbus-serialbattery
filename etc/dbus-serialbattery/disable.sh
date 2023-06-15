#!/bin/bash

# remove comment for easier troubleshooting
#set -x

# handle read only mounts
bash /opt/victronenergy/swupdate-scripts/remount-rw.sh

# remove driver from serial starter
rm -f /data/conf/serial-starter.d/dbus-serialbattery.conf
# kill serial starter, to reload changes
pkill -f "/opt/victronenergy/serial-starter/serial-starter.sh"

# remove services
rm -rf /service/dbus-serialbattery.*
rm -rf /service/dbus-blebattery.*

# kill driver, if running
pkill -f "dbus-serialbattery"
pkill -f "dbus-blebattery"

# remove install script from rc.local
sed -i "/bash \/data\/etc\/dbus-serialbattery\/reinstall-local.sh/d" /data/rc.local

# remove cronjob
sed -i "/5 0,12 \* \* \* \/etc\/init.d\/bluetooth restart/d" /var/spool/cron/root


### needed for upgrading from older versions | start ###
# remove old drivers before changing from dbus-blebattery-$1 to dbus-blebattery.$1
rm -rf /service/dbus-blebattery-*
# remove old install script from rc.local
sed -i "/sh \/data\/etc\/dbus-serialbattery\/reinstalllocal.sh/d" /data/rc.local
sed -i "/sh \/data\/etc\/dbus-serialbattery\/reinstall-local.sh/d" /data/rc.local
# remove old entry from rc.local
sed -i "/sh \/data\/etc\/dbus-serialbattery\/installble.sh/d" /data/rc.local
### needed for upgrading from older versions | end ###

echo "The dbus-serialbattery driver was disabled".
echo
