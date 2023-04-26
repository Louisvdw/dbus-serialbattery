#!/bin/bash

# remove comment for easier troubleshooting
#set -x

# install required packages
# TO DO: Check first if packages are already installed
opkg update
opkg install python3-misc python3-pip
pip3 install bleak

# setup cronjob to restart Bluetooth
grep -qxF "5 0,12 * * * /etc/init.d/bluetooth restart" /var/spool/cron/root || echo "5 0,12 * * * /etc/init.d/bluetooth restart" >> /var/spool/cron/root

# add install-script to rc.local to be ready for firmware update
filename=/data/rc.local
if [ ! -f $filename ]; then
    echo "#!/bin/bash" >> $filename
    chmod 755 $filename
fi
grep -qxF "sh /data/etc/dbus-serialbattery/installble.sh" $filename || echo "sh /data/etc/dbus-serialbattery/installble.sh" >> $filename

install_service() {
    mkdir -p /service/dbus-blebattery-$1/log
    echo "#!/bin/sh" > /service/dbus-blebattery-$1/log/run
    echo "exec multilog t s25000 n4 /var/log/dbus-blebattery-$1" >> /service/dbus-blebattery-$1/log/run
    chmod 755 /service/dbus-blebattery-$1/log/run

    echo "#!/bin/sh" > /service/dbus-blebattery-$1/run
    echo "exec 2>&1" >> /service/dbus-blebattery-$1/run
    echo "bluetoothctl disconnect $3" >> /service/dbus-blebattery-$1/run
    echo "python /data/etc/dbus-serialbattery/dbus-serialbattery.py $2 $3" >> /service/dbus-blebattery-$1/run
    chmod 755 /service/dbus-blebattery-$1/run
}


## CONFIG AREA

## Uncomment for each adapter here, increase the number for each adapter/service

install_service 0 Jkbms_Ble C8:47:8C:E8:12:04
# install_service 0 Jkbms_Ble C8:47:8C:12:34:56
# install_service 1 Jkbms_Ble C8:47:8C:78:9A:BC
