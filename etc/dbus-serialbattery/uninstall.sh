#!/bin/bash

# remove comment for easier troubleshooting
#set -x

# disable driver
bash /data/etc/dbus-serialbattery/disable.sh


# remove files in Victron directory. Don't use variables here,
# since on an error the whole /opt/victronenergy gets deleted
rm -rf /opt/victronenergy/service/dbus-serialbattery
rm -rf /opt/victronenergy/service-templates/dbus-serialbattery
rm -rf /opt/victronenergy/dbus-serialbattery


# restore GUI changes
/data/etc/dbus-serialbattery/restore-gui.sh


# uninstall modules
read -r -p "Do you want to uninstall bleak, python-can, python3-pip and python3-modules? If you don't know just press enter. [y/N] " response
echo
response=${response,,} # tolower
if [[ $response =~ ^(y) ]]; then
    echo "Uninstalling modules..."
    pip3 uninstall bleak
    pip3 uninstall python-can
    opkg remove python3-pip python3-modules
    echo "done."
    echo
fi


read -r -p "Do you want to delete the install and configuration files in \"/data/etc/dbus-serialbattery\"? If you don't know just press enter. [y/N] " response
echo
response=${response,,} # tolower
if [[ $response =~ ^(y) ]]; then
    rm -rf /data/etc/dbus-serialbattery
    echo "The folder \"/data/etc/dbus-serialbattery\" was removed."
    echo
fi


echo "The dbus-serialbattery driver was uninstalled. Please reboot."
echo
