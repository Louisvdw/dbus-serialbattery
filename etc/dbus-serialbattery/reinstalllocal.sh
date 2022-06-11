#!/bin/sh
mkdir /opt/victronenergy/dbus-serialbattery
mkdir /opt/victronenergy/service-templates/dbus-serialbattery
cp /data/etc/dbus-serialbattery/* /opt/victronenergy/dbus-serialbattery
cp -r /data/etc/dbus-serialbattery/service/* /opt/victronenergy/service-templates/dbus-serialbattery