#!/bin/bash
set -x
#restore original backup
if [ -f /opt/victronenergy/gui/qml/PageBattery.qml.backup ]; then
    cp -f /opt/victronenergy/gui/qml/PageBattery.qml.backup /opt/victronenergy/gui/qml/PageBattery.qml
    echo "PageBattery.qml was restored."
fi
# backup old PageLynxIonIo.qml once. New firmware upgrade will remove the backup
if [ -f /opt/victronenergy/gui/qml/PageLynxIonIo.qml.backup ]; then
    cp -f /opt/victronenergy/gui/qml/PageLynxIonIo.qml.backup /opt/victronenergy/gui/qml/PageLynxIonIo.qml
    echo "PageLynxIonIo.qml was restored."
fi

#stop gui
svc -d /service/gui
#sleep 1 sec
sleep 1
#start gui
svc -u /service/gui
