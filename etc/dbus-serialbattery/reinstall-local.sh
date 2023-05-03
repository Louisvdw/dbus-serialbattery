#!/bin/bash

# remove comment for easier troubleshooting
#set -x

DRIVERNAME=dbus-serialbattery

# handle read only mounts
bash /opt/victronenergy/swupdate-scripts/remount-rw.sh

# install
rm -rf /opt/victronenergy/service/$DRIVERNAME
rm -rf /opt/victronenergy/service-templates/$DRIVERNAME
rm -rf /opt/victronenergy/$DRIVERNAME
mkdir /opt/victronenergy/$DRIVERNAME
mkdir /opt/victronenergy/$DRIVERNAME/bms
cp -f /data/etc/$DRIVERNAME/* /opt/victronenergy/$DRIVERNAME &>/dev/null
cp -f /data/etc/$DRIVERNAME/bms/* /opt/victronenergy/$DRIVERNAME/bms &>/dev/null
cp -rf /data/etc/$DRIVERNAME/service /opt/victronenergy/service-templates/$DRIVERNAME
bash /data/etc/$DRIVERNAME/install-qml.sh

# check if serial-starter.d was deleted
serialstarter_path="/data/conf/serial-starter.d"
serialstarter_file="$serialstarter_path/dbus-serialbattery.conf"

# check if folder is a file (older versions of this driver)
if [ -f $serialstarter_path ]; then
    rm -f $serialstarter_path
fi

# check if folder exists
if [ ! -d $serialstarter_path ]; then
    mkdir $serialstarter_path
fi

# check if file exists
if [ ! -f $serialstarter_file ]; then
    echo "service sbattery        dbus-serialbattery" >> $serialstarter_file
    echo "alias default gps:vedirect:sbattery" >> $serialstarter_file
    echo "alias rs485 cgwacs:fzsonick:imt:modbus:sbattery" >> $serialstarter_file
fi

# add install-script to rc.local to be ready for firmware update
filename=/data/rc.local
if [ ! -f $filename ]; then
    echo "#!/bin/bash" >> $filename
    chmod 755 $filename
fi
grep -qxF "sh /data/etc/$DRIVERNAME/reinstall-local.sh" $filename || echo "sh /data/etc/$DRIVERNAME/reinstall-local.sh" >> $filename

# add empty config.ini, if it does not exist to make it easier for users to add custom settings
filename=/data/etc/$DRIVERNAME/config.ini
if [ ! -f $filename ]; then
    echo "[DEFAULT]" > $filename
    echo "" >> $filename
    echo "; If you want to add custom settings, then check the settings you want to change in \"config.default.ini\"" >> $filename
    echo "; and add them below to persist future driver updates." >> $filename
fi


### needed for upgrading from older versions | start ###
# remove old install script from rc.local
sed -i "/sh \/data\/etc\/$DRIVERNAME\/reinstalllocal.sh/d" /data/rc.local
### needed for upgrading from older versions | end ###


# restart if running
pkill -f "python .*/$DRIVERNAME.py"

# install notes
echo
echo "SERIAL battery connection: The installation is complete. You don't have to do anything more."
echo
echo "CUSTOM SETTINGS: If you want to add custom settings, then check the settings you want to change in \"config.default.ini\" and add them to \"config.ini\" to persist future driver updates."
echo
echo
