#!/bin/sh
#backup old PageBattery.qml once. New firmware upgrade will remove the backup
if [ ! -f /opt/victronenergy/gui/qml/PageBattery.qml.backup ]; then
    cp /opt/victronenergy/gui/qml/PageBattery.qml /opt/victronenergy/gui/qml/PageBattery.qml.backup
fi
if [ ! -f /opt/victronenergy/gui/qml/PageLynxIonIo.qml.backup ]; then
    cp /opt/victronenergy/gui/qml/PageLynxIonIo.qml /opt/victronenergy/gui/qml/PageLynxIonIo.qml.backup
fi
#copy new PageBattery.qml
cp /data/etc/dbus-serialbattery/qml/PageBattery.qml /opt/victronenergy/gui/qml/
#copy new PageLynxIonIo.qml
cp /data/etc/dbus-serialbattery/qml/PageLynxIonIo.qml /opt/victronenergy/gui/qml/
#copy new PageBatteryCellVoltages
cp /data/etc/dbus-serialbattery/qml/PageBatteryCellVoltages.qml /opt/victronenergy/gui/qml/
cp /data/etc/dbus-serialbattery/qml/PageBatterySetup.qml /opt/victronenergy/gui/qml/
#stop gui
svc -d /service/gui
#sleep 1 sec
sleep 1
#start gui
svc -u /service/gui
