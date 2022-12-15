#!/bin/sh

#restore original backup 
cp -f /opt/victronenergy/gui/qml/PageBattery.qml.backup /opt/victronenergy/gui/qml/PageBattery.qml

#stop gui
svc -d /service/gui
#sleep 1 sec
sleep 1
#start gui
svc -u /service/gui
