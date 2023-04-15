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
echo "BLUETOOTH battery connection: There are a few more steps to complete installation."
echo "    1. Make sure to disable Settings -> Bluetooth in the Remote-Console to prevent reconnects every minute."
echo "    2. Put your Bluetooth MAC adress in \"/data/etc/dbus-serialbattery/installble.sh\" and make sure to uncomment at least one install_service line at the bottom of the file."
echo "    3. Execute \"/data/etc/dbus-serialbattery/installble.sh\" once to create services for each Bluetooth BMS."
echo "    ATTENTION!"
echo "    If you changed the default connection PIN of your BMS, then you have to pair the BMS first using OS tools like the \"bluetoothctl\"."
echo "    See https://wiki.debian.org/BluetoothUser#Using_bluetoothctl for more details."
echo
echo "CUSTOM SETTINGS: If you want to add custom settings, then check the settings you want to change in \"config.default.ini\" and add them to \"config.ini\" to persist future driver updates."
echo
echo
