#!/bin/sh

# remove comment for easier troubleshooting
#set -x

# extract driver
tar -zxf ./venus-data.tar.gz -C /data

# install driver
sh /data/etc/dbus-serialbattery/reinstalllocal.sh

echo
echo "SERIAL battery connection: The installation is complete. You don't have to do anything more."
echo
echo "CUSTOM SETTINGS: If you want to add custom settings, then check the settings you want to change in \"config.default.ini\" and add them to \"config.ini\" to persist future driver updates."
echo
echo
