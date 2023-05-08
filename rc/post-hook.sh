#!/bin/bash

# executed after archive extraction on USB install
# see https://github.com/victronenergy/meta-victronenergy/blob/15fa33c3e5430f7c08a688dc02171f5be9a81c84/meta-venus/recipes-core/initscripts/files/update-data.sh#L43


# search for config.ini in USB root and copy it, if found
for dir in /media/*; do
    if [ -f "/media/$dir/config.ini" ]; then
        cp -f /media/$dir/config.ini /data/etc/dbus-serialbattery/config.ini

        # remove backup config.ini
        if [ -f "/data/etc/dbus-serialbattery_config.ini.backup" ]; then
            rm /data/etc/dbus-serialbattery_config.ini.backup
        fi
    fi
done

# restore config.ini
if [ -f "/data/etc/dbus-serialbattery_config.ini.backup" ]; then
    mv /data/etc/dbus-serialbattery_config.ini.backup /data/etc/dbus-serialbattery/config.ini
fi

# run reinstall local
bash /data/etc/dbus-serialbattery/reinstall-local.sh
