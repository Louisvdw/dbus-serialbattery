#!/bin/sh

DRIVER=/opt/victronenergy/dbus-serialbattery
RUN=/opt/victronenergy/service-templates/dbus-serialbattery
OLD=/opt/victronenergy/service/dbus-serialbattery

#/dev/mmcblk1p3 mountpoint / was made read only in 2.91 release
mount -o remount,rw /dev/mmcblk1p3 /

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
if [ -d "$OLD" ]; then
  if [ -L "$OLD" ]; then
    # Remove old SymLink.
    rm "$RUN"
  fi
fi

cp -f /data/etc/dbus-serialbattery/* /opt/victronenergy/dbus-serialbattery
cp -rf /data/etc/dbus-serialbattery/service/* /opt/victronenergy/service-templates/dbus-serialbattery
