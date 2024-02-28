#!/bin/bash

# remove comment for easier troubleshooting
#set -x

# elaborate version string for better comparing
# https://github.com/kwindrem/SetupHelper/blob/ebaa65fcf23e2bea6797f99c1c41174143c1153c/updateFileSets#L56-L81
function versionStringToNumber ()
{
    local p4="" ; local p5="" ; local p5=""
    local major=""; local minor=""

	# first character should be 'v' so first awk parameter will be empty and is not prited into the read command
	#
	# version number formats: v2.40, v2.40~6, v2.40-large-7, v2.40~6-large-7
	# so we must adjust how we use paramters read from the version string
	# and parsed by awk
	# if no beta make sure release is greater than any beta (i.e., a beta portion of 999)

    read major minor p4 p5 p6 <<< $(echo $1 | awk -v FS='[v.~-]' '{print $2, $3, $4, $5, $6}')
	((versionNumber = major * 1000000000 + minor * 1000000))
	if [ -z $p4 ] || [ $p4 = "large" ]; then
        ((versionNumber += 999))
	else
		((versionNumber += p4))
    fi
	if [ ! -z $p4 ] && [ $p4 = "large" ]; then
		((versionNumber += p5 * 1000))
		large=$p5
	elif [ ! -z $p6 ]; then
		((versionNumber += p6 * 1000))
	fi
}

# backup old PageBattery.qml once. New firmware upgrade will remove the backup
if [ ! -f /opt/victronenergy/gui/qml/PageBattery.qml.backup ]; then
    cp /opt/victronenergy/gui/qml/PageBattery.qml /opt/victronenergy/gui/qml/PageBattery.qml.backup
fi
# backup old PageBatteryParameters.qml once. New firmware upgrade will remove the backup
if [ ! -f /opt/victronenergy/gui/qml/PageBatteryParameters.qml.backup ]; then
    cp /opt/victronenergy/gui/qml/PageBatteryParameters.qml /opt/victronenergy/gui/qml/PageBatteryParameters.qml.backup
fi
# backup old PageBatterySettings.qml once. New firmware upgrade will remove the backup
if [ ! -f /opt/victronenergy/gui/qml/PageBatterySettings.qml.backup ]; then
    cp /opt/victronenergy/gui/qml/PageBatterySettings.qml /opt/victronenergy/gui/qml/PageBatterySettings.qml.backup
fi
# backup old PageLynxIonIo.qml once. New firmware upgrade will remove the backup
if [ ! -f /opt/victronenergy/gui/qml/PageLynxIonIo.qml.backup ]; then
    cp /opt/victronenergy/gui/qml/PageLynxIonIo.qml /opt/victronenergy/gui/qml/PageLynxIonIo.qml.backup
fi

# count changed files
filesChanged=0

# copy new PageBattery.qml if changed
if ! cmp -s /data/etc/dbus-serialbattery/qml/PageBattery.qml /opt/victronenergy/gui/qml/PageBattery.qml
then
    cp /data/etc/dbus-serialbattery/qml/PageBattery.qml /opt/victronenergy/gui/qml/
    ((filesChanged++))
fi

# copy new PageBatteryCellVoltages if changed
if ! cmp -s /data/etc/dbus-serialbattery/qml/PageBatteryCellVoltages.qml /opt/victronenergy/gui/qml/PageBatteryCellVoltages.qml
then
    cp /data/etc/dbus-serialbattery/qml/PageBatteryCellVoltages.qml /opt/victronenergy/gui/qml/
    ((filesChanged++))
fi

# copy new PageBatteryParameters.qml if changed
if ! cmp -s /data/etc/dbus-serialbattery/qml/PageBatteryParameters.qml /opt/victronenergy/gui/qml/PageBatteryParameters.qml
then
    cp /data/etc/dbus-serialbattery/qml/PageBatteryParameters.qml /opt/victronenergy/gui/qml/
    ((filesChanged++))
fi

# copy new PageBatterySettings.qml if changed
if ! cmp -s /data/etc/dbus-serialbattery/qml/PageBatterySettings.qml /opt/victronenergy/gui/qml/PageBatterySettings.qml
then
    cp /data/etc/dbus-serialbattery/qml/PageBatterySettings.qml /opt/victronenergy/gui/qml/
    ((filesChanged++))
fi

# copy new PageBatterySetup if changed
if ! cmp -s /data/etc/dbus-serialbattery/qml/PageBatterySetup.qml /opt/victronenergy/gui/qml/PageBatterySetup.qml
then
    cp /data/etc/dbus-serialbattery/qml/PageBatterySetup.qml /opt/victronenergy/gui/qml/
    ((filesChanged++))
fi

# copy new PageLynxIonIo.qml if changed
if ! cmp -s /data/etc/dbus-serialbattery/qml/PageLynxIonIo.qml /opt/victronenergy/gui/qml/PageLynxIonIo.qml
then
    cp /data/etc/dbus-serialbattery/qml/PageLynxIonIo.qml /opt/victronenergy/gui/qml/
    ((filesChanged++))
fi


# get current Venus OS version
versionStringToNumber $(head -n 1 /opt/victronenergy/version)
((venusVersionNumber = $versionNumber))

# revert to VisualItemModel, if Venus OS older than v3.00~14 (v3.00~14 uses VisibleItemModel)
versionStringToNumber "v3.00~14"

# change in Victron directory, else the files are "broken" if upgrading from v2 to v3
qmlDir="/opt/victronenergy/gui/qml"

if (( $venusVersionNumber < $versionNumber )); then
    echo -n "Venus OS $(head -n 1 /opt/victronenergy/version) is older than v3.00~14. Replacing VisibleItemModel with VisualItemModel... "
    fileList="$qmlDir/PageBattery.qml"
    fileList+=" $qmlDir/PageBatteryCellVoltages.qml"
    fileList+=" $qmlDir/PageBatteryParameters.qml"
    fileList+=" $qmlDir/PageBatterySettings.qml"
    fileList+=" $qmlDir/PageBatterySetup.qml"
    fileList+=" $qmlDir/PageLynxIonIo.qml"
    for file in $fileList ; do
        sed -i -e 's/VisibleItemModel/VisualItemModel/' "$file"
	done
    echo "done."
fi

# if files changed, restart gui
if [ $filesChanged -gt 0 ]; then
    # stop gui
    svc -d /service/gui
    # sleep 1 sec
    sleep 1
    # start gui
    svc -u /service/gui
    echo "New QML files were installed and the GUI was restarted."
fi
