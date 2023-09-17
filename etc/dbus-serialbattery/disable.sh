#!/bin/bash

# remove comment for easier troubleshooting
#set -x

# handle read only mounts
bash /opt/victronenergy/swupdate-scripts/remount-rw.sh

# remove driver from serial starter
rm -f /data/conf/serial-starter.d/dbus-serialbattery.conf
# remove serial-starter.d if empty
rmdir /data/conf/serial-starter.d >/dev/null 2>&1
# kill serial starter, to reload changes
pkill -f "/opt/victronenergy/serial-starter/serial-starter.sh"

# remove services
rm -rf /service/dbus-serialbattery.*
rm -rf /service/dbus-blebattery.*
rm -rf /service/dbus-canbattery.*

# kill driver, if running
# serial
pkill -f "supervise dbus-serialbattery.*"
pkill -f "multilog .* /var/log/dbus-serialbattery.*"
pkill -f "python .*/dbus-serialbattery.py /dev/tty.*"
# bluetooth
pkill -f "supervise dbus-blebattery.*"
pkill -f "multilog .* /var/log/dbus-blebattery.*"
pkill -f "python .*/dbus-serialbattery.py .*_Ble.*"
# can
pkill -f "supervise dbus-canbattery.*"
pkill -f "multilog .* /var/log/dbus-canbattery.*"
pkill -f "python .*/dbus-serialbattery.py can.*"

# remove install script from rc.local
sed -i "/bash \/data\/etc\/dbus-serialbattery\/reinstall-local.sh/d" /data/rc.local

# remove cronjob
sed -i "/5 0,12 \* \* \* \/etc\/init.d\/bluetooth restart/d" /var/spool/cron/root >/dev/null 2>&1


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
