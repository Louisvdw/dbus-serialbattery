#!/bin/bash
set -x

## DO NOT TOUCH THIS ##
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
## END DO NOT TOUCH AREA ##

## Uncomment for each adapter here, increase the number for each service

# install_service 0 Jkbms_Ble C8:47:8C:12:34:56
# install_service 1 Jkbms_Ble C8:47:8C:78:9A:BC
