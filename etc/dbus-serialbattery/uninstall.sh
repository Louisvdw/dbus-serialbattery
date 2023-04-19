#!/bin/bash

# remove comment for easier troubleshooting
#set -x

DRIVERNAME=dbus-serialbattery

# handle read only mounts
sh /opt/victronenergy/swupdate-scripts/remount-rw.sh

# remove files
rm -f /data/conf/serial-starter.d/$DRIVERNAME.conf
rm -rf /opt/victronenergy/service/$DRIVERNAME
rm -rf /opt/victronenergy/service-templates/$DRIVERNAME
rm -rf /opt/victronenergy/$DRIVERNAME
rm -rf /service/dbus-blebattery-*

# kill if running
pkill -f "python .*/$DRIVERNAME.py"

# remove install-script from rc.local
sed -i "/sh \/data\/etc\/$DRIVERNAME\/reinstalllocal.sh/d" /data/rc.local
sed -i "/sh \/data\/etc\/$DRIVERNAME\/installble.sh/d" /data/rc.local

# remove cronjob
sed -i "/5 0,12 \* \* \* \/etc\/init.d\/bluetooth restart/d" /var/spool/cron/root

# uninstall modules
read -r -p "Do you also want to uninstall bleak, python3-pip and python3-modules? If you don't know select y. [Y/n] " response
echo
response=${response,,} # tolower
if [[ $response =~ ^(y| ) ]] || [[ -z $response ]]; then
    echo "Uninstalling modules..."
    pip3 uninstall bleak
    opkg remove python3-pip python3-modules
    echo "done."
    echo
fi
