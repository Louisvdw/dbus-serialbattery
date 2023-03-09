#!/bin/sh

# install required packages
opkg update
opkg install python3-misc python3-pip
pip3 install bleak

# install driver
tar -zxf ./venus-data.tar.gz -C /data
sh /data/etc/dbus-serialbattery/reinstalllocal.sh

# setup cronjob to restart Bluetooth
grep -qxF "5 0,12 * * * /etc/init.d/bluetooth restart" /var/spool/cron/root || echo "5 0,12 * * * /etc/init.d/bluetooth restart" >> /var/spool/cron/root


echo "Make sure to disable Settings -> Bluetooth in the Remote-Console to prevent reconnects every minute."
echo "ATTENTION!"
echo "- At the moment this driver needs a serial to USB adapter attached to start. The serial side hasn't to be connected anywhere."
echo "- If you changed the default connection PIN of JKBMS, then you have to pair the JKBMS first using OS tools like the \"bluetoothctl\"."
echo "See https://wiki.debian.org/BluetoothUser#Using_bluetoothctl for more details."
