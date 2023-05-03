#!/bin/bash

# remove comment for easier troubleshooting
#set -x

PS3="Select the branch from wich you want to install the current code (possible bugs included): "

select branch in master jkbms_ble quit
do
    case $branch in
        master)
            echo "Selected branch: $branch"
            #echo "Selected number: $REPLY"
            break
            ;;
        jkbms_ble)
            echo "Selected branch: $branch"
            #echo "Selected number: $REPLY"
            break
            ;;
        quit)
            exit 0
            ;;
        *)
            echo "Invalid option $REPLY"
            ;;
    esac
done


cd /tmp

# clean already extracted folder
rm -rf /tmp/dbus-serialbattery-$branch

# download driver
wget -O $branch.zip https://github.com/Louisvdw/dbus-serialbattery/archive/refs/heads/$branch.zip

# extract archive
unzip -q $branch.zip

# backup config.ini
if [ -f "/data/etc/dbus-serialbattery/config.ini" ]; then
    mv /data/etc/dbus-serialbattery/config.ini /data/etc/config.ini
fi

# remove old driver
rm -rf /data/etc/dbus-serialbattery

# copy driver
cp -rf /tmp/dbus-serialbattery-$branch/etc/dbus-serialbattery/ /data/etc

# restore config.ini
if [ -f "/data/etc/config.ini" ]; then
    mv /data/etc/config.ini /data/etc/dbus-serialbattery/config.ini
fi

# set permissions
chmod +x /data/etc/dbus-serialbattery/*.sh
chmod +x /data/etc/dbus-serialbattery/*.py
chmod +x /data/etc/dbus-serialbattery/service/run
chmod +x /data/etc/dbus-serialbattery/service/log/run

# run install script
bash /data/etc/dbus-serialbattery/reinstall-local.sh
