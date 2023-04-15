#!/bin/sh
set -x

# install driver
tar -zxf ./venus-data.tar.gz -C /data
sh /data/etc/dbus-serialbattery/reinstalllocal.sh

echo "SERIAL battery connection: The installation is complete. You don't have to do anything more."
echo
echo "BLUETOOTH battery connection: There are a few more steps to complete installation."
echo "1. Make sure to disable Settings -> Bluetooth in the Remote-Console to prevent reconnects every minute."
echo "2. Put your Bluetooth MAC adress in \"/data/etc/dbus-serialbattery/installble.sh\" and make sure to uncomment at least one install_service line at the bottom of the file."
echo "3. Execute \"/data/etc/dbus-serialbattery/installble.sh\" once to create"
echo "ATTENTION!"
echo "- If you changed the default connection PIN of JKBMS, then you have to pair the JKBMS first using OS tools like the \"bluetoothctl\"."
echo "See https://wiki.debian.org/BluetoothUser#Using_bluetoothctl for more details."
echo
echo "CUSTOM SETTINGS: If you want to add custom settings, then check the settings you want to change in \"config.default.ini\" and add them to \"config.ini\" to persist future driver updates."
