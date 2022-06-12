#!/bin/sh

$DRIVER = "/opt/victronenergy/dbus-serialbattery"
$RUN = "/opt/victronenergy/service-templates/dbus-serialbattery"
if [ -d "$DRIVER" ]; then 
  if [ -L "$DRIVER" ]; then
    # Remove old SymLink.
    rm "$DRIVER"
    # Create as folder
    mkdir "$DRIVER"
  fi
else
  # Create folder
  mkdir "$DRIVER"
fi
if [ -d "$RUN" ]; then 
  if [ -L "$RUN" ]; then
    # Remove old SymLink.
    rm "$RUN"
    # Create as folder
    mkdir "$RUN"
  fi
else
  # Create folder
  mkdir "$RUN"
fi

cp -f /data/etc/dbus-serialbattery/* /opt/victronenergy/dbus-serialbattery
cp -rf /data/etc/dbus-serialbattery/service/* /opt/victronenergy/service-templates/dbus-serialbattery