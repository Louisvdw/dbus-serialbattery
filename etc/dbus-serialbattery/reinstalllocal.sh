#!/bin/sh

DRIVERNAME=dbus-serialbattery

#handle read only mounts
sh /opt/victronenergy/swupdate-scripts/remount-rw.sh

#install
rm -rf /opt/victronenergy/service/$DRIVERNAME
rm -rf /opt/victronenergy/service-templates/$DRIVERNAME
rm -rf /opt/victronenergy/$DRIVERNAME
mkdir /opt/victronenergy/$DRIVERNAME
cp -f /data/etc/$DRIVERNAME/* /opt/victronenergy/$DRIVERNAME &>/dev/null
cp -rf /data/etc/$DRIVERNAME/service /opt/victronenergy/service-templates/$DRIVERNAME
sh /data/etc/$DRIVERNAME/installqml.sh

#restart if running
pkill -f "python .*/$DRIVERNAME.py"

# add install-script to rc.local to be ready for firmware update
filename=/data/rc.local
if [ ! -f $filename ]; then
    echo "#!/bin/bash" >> $filename
    chmod 755 $filename
fi
grep -qxF "sh /data/etc/$DRIVERNAME/reinstalllocal.sh" $filename || echo "sh /data/etc/$DRIVERNAME/reinstalllocal.sh" >> $filename

