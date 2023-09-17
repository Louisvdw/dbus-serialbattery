#!/bin/bash

# remove comment for easier troubleshooting
#set -x


# check if minimum required Venus OS is installed | start
versionRequired="v2.90"

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

# get current Venus OS version
versionStringToNumber "$(head -n 1 /opt/victronenergy/version)"
venusVersionNumber="$versionNumber"

# minimum required version to install the driver
versionStringToNumber "$versionRequired"

if (( $venusVersionNumber < $versionNumber )); then
    echo
    echo
    echo "Minimum required Venus OS version \"$versionRequired\" not met. Currently version \"$(head -n 1 /opt/victronenergy/version)\" is installed."
    echo
    echo "Please update via \"Remote Console/GUI -> Settings -> Firmware -> Online Update\""
    echo "OR"
    echo "by executing \"/opt/victronenergy/swupdate-scripts/check-updates.sh -update -force\""
    echo
    echo "Install the driver again after Venus OS was updated."
    echo
    echo
    exit 1
fi
# check if minimum required Venus OS is installed | end


# handle read only mounts
bash /opt/victronenergy/swupdate-scripts/remount-rw.sh

# install
rm -rf /opt/victronenergy/service/dbus-serialbattery
rm -rf /opt/victronenergy/service-templates/dbus-serialbattery
rm -rf /opt/victronenergy/dbus-serialbattery
mkdir /opt/victronenergy/dbus-serialbattery
mkdir /opt/victronenergy/dbus-serialbattery/bms
cp -f /data/etc/dbus-serialbattery/* /opt/victronenergy/dbus-serialbattery &>/dev/null
cp -f /data/etc/dbus-serialbattery/bms/* /opt/victronenergy/dbus-serialbattery/bms &>/dev/null
cp -rf /data/etc/dbus-serialbattery/service /opt/victronenergy/service-templates/dbus-serialbattery
bash /data/etc/dbus-serialbattery/install-qml.sh

# check if serial-starter.d was deleted
serialstarter_path="/data/conf/serial-starter.d"
serialstarter_file="$serialstarter_path/dbus-serialbattery.conf"

# check if folder is a file (older versions of this driver < v1.0.0)
if [ -f "$serialstarter_path" ]; then
    rm -f "$serialstarter_path"
fi

# check if folder exists
if [ ! -d "$serialstarter_path" ]; then
    mkdir "$serialstarter_path"
fi

# check if file exists
if [ ! -f "$serialstarter_file" ]; then
    {
        echo "service sbattery        dbus-serialbattery"
        echo "alias default gps:vedirect:sbattery"
        echo "alias rs485 cgwacs:fzsonick:imt:modbus:sbattery"
    } > "$serialstarter_file"
fi

# add install-script to rc.local to be ready for firmware update
filename=/data/rc.local
if [ ! -f "$filename" ]; then
    echo "#!/bin/bash" > "$filename"
    chmod 755 "$filename"
fi
grep -qxF "bash /data/etc/dbus-serialbattery/reinstall-local.sh" $filename || echo "bash /data/etc/dbus-serialbattery/reinstall-local.sh" >> $filename

# add empty config.ini, if it does not exist to make it easier for users to add custom settings
filename="/data/etc/dbus-serialbattery/config.ini"
if [ ! -f "$filename" ]; then
    {
        echo "[DEFAULT]"
        echo
        echo "; If you want to add custom values/settings, then check the values/settings you want to change in \"config.default.ini\""
        echo "; and insert them below to persist future driver updates."
        echo
        echo "; Example (remove the semicolon \";\" to uncomment and activate the value/setting):"
        echo "; MAX_BATTERY_CHARGE_CURRENT = 50.0"
        echo "; MAX_BATTERY_DISCHARGE_CURRENT = 60.0"
        echo
        echo
    } > $filename
fi

# kill driver, if running. It gets restarted by the service daemon
pkill -f "supervise dbus-serialbattery.*"
pkill -f "multilog .* /var/log/dbus-serialbattery.*"
pkill -f "python .*/dbus-serialbattery.py /dev/tty.*"



### BLUETOOTH PART | START ###

# get BMS list from config file
bluetooth_bms=$(awk -F "=" '/^BLUETOOTH_BMS/ {print $2}' /data/etc/dbus-serialbattery/config.ini)
#echo $bluetooth_bms

# clear whitespaces
bluetooth_bms_clean="$(echo $bluetooth_bms | sed 's/\s*,\s*/,/g')"
#echo $bluetooth_bms_clean

# split into array
IFS="," read -r -a bms_array <<< "$bluetooth_bms_clean"
#declare -p bms_array
# readarray -td, bms_array <<< "$bluetooth_bms_clean,"; unset 'bms_array[-1]'; declare -p bms_array;

bluetooth_length=${#bms_array[@]}
# echo $bluetooth_length

# stop all dbus-blebattery services, if at least one exists
if [ -d "/service/dbus-blebattery.0" ]; then
    svc -u /service/dbus-blebattery.*

    # always remove existing blebattery services to cleanup
    rm -rf /service/dbus-blebattery.*

    # kill all blebattery processes that remain
    pkill -f "supervise dbus-blebattery.*"
    pkill -f "multilog .* /var/log/dbus-blebattery.*"
    pkill -f "python .*/dbus-serialbattery.py .*_Ble"

    # kill opened bluetoothctl processes
    pkill -f "^bluetoothctl "
fi


if [ "$bluetooth_length" -gt 0 ]; then

    echo
    echo "Found $bluetooth_length Bluetooth BMS in the config file!"
    echo

    /etc/init.d/bluetooth stop
    echo

    # install required packages
    # TO DO: Check first if packages are already installed
    echo "Installing required packages to use Bluetooth connection..."

    # dbus-fast: skip compiling/building the wheel
    # else weak system crash and are not able to install it,
    # see https://github.com/Bluetooth-Devices/dbus-fast/issues/237
    # and https://github.com/Louisvdw/dbus-serialbattery/issues/785
    export SKIP_CYTHON=false

    opkg update
    opkg install python3-misc python3-pip

    echo
    pip3 install bleak

    # # ONLY FOR TESTING if there are version issues
    # echo
    # echo "Available bleak versions:"
    # curl --silent https://api.github.com/repos/hbldh/bleak/releases | grep '"name": "v' | sed "s/    \"name\": \"v//g" | sed "s/\",//g"
    # echo
    # read -r -p "Specify the bleak version to install: " bleak_version
    # pip3 install bleak=="$bleak_version"
    # echo
    # echo
    # echo "Available dbus-fast versions:"
    # curl --silent https://api.github.com/repos/Bluetooth-Devices/dbus-fast/releases | grep '"name": "v' | sed "s/    \"name\": \"v//g" | sed "s/\",//g"
    # echo
    # read -r -p "Specify the dbus-fast version to install: " dbus_fast_version
    # pip3 install dbus-fast=="$dbus_fast_version"
    # echo

    echo "done."
    echo

    /etc/init.d/bluetooth start
    echo

    # function to install ble battery
    install_blebattery_service() {
        if [ -z "$1" ]; then
            echo "ERROR: BMS unique number is empty. Aborting installation."
            echo
            exit 1
        fi
        if [ -z "$2" ]; then
            echo "ERROR: BMS type for battery $1 is empty. Aborting installation."
            echo
            exit 1
        fi
        if [ -z "$3" ]; then
            echo "ERROR: BMS MAC address for battery $1 with BMS type $2 is empty. Aborting installation."
            echo
            exit 1
        fi

        echo "Installing \"$2\" with MAC address \"$3\" as dbus-blebattery.$1"

        mkdir -p "/service/dbus-blebattery.$1/log"
        {
            echo "#!/bin/sh"
            echo "exec multilog t s25000 n4 /var/log/dbus-blebattery.$1"
        } > "/service/dbus-blebattery.$1/log/run"
        chmod 755 "/service/dbus-blebattery.$1/log/run"

        {
            echo "#!/bin/sh"
            echo "exec 2>&1"
            echo "echo"
            echo "echo \"INFO:Bluetooth details\""
            # close all open connections, else the driver can't connect
            echo "bluetoothctl disconnect $3"

            # enable bluetoothctl scan in background to display signal strength (RSSI), else it's missing
            echo "bluetoothctl scan on | grep \"$3\" | grep \"RSSI\" &"
            # with multiple Bluetooth BMS one scan for all should be enough. Check if that can be changed globally, maybe with a cronjob after reboot?
            # echo "bluetoothctl scan on > /dev/null &"

            # wait 5 seconds to finish the scan
            echo "sleep 5"
            # display some Bluetooth device details
            echo "bluetoothctl info $3 | grep -E \"Device|Alias|Pair|Trusted|Blocked|Connected|RSSI|Power\""
            echo "echo"
            echo "python /opt/victronenergy/dbus-serialbattery/dbus-serialbattery.py $2 $3"
            echo "pkill -f \"bluetoothctl scan on\""
        } > "/service/dbus-blebattery.$1/run"
        chmod 755 "/service/dbus-blebattery.$1/run"
    }

    # Example
    # install_blebattery_service 0 Jkbms_Ble C8:47:8C:00:00:00
    # install_blebattery_service 1 Jkbms_Ble C8:47:8C:00:00:11

    for (( i=0; i<bluetooth_length; i++ ));
    do
        # split BMS type and MAC address
        IFS=' ' read -r -a bms <<< "${bms_array[$i]}"
        install_blebattery_service $i "${bms[0]}" "${bms[1]}"
    done

    echo

    # setup cronjob to restart Bluetooth
    # remove if not needed anymore, has to be checked first --> seems that it's not needed anymore
    # grep -qxF "5 0,12 * * * /etc/init.d/bluetooth restart" /var/spool/cron/root || echo "5 0,12 * * * /etc/init.d/bluetooth restart" >> /var/spool/cron/root

    # remove cronjob
    sed -i "/5 0,12 \* \* \* \/etc\/init.d\/bluetooth restart/d" /var/spool/cron/root >/dev/null 2>&1

else

    # remove cronjob
    sed -i "/5 0,12 \* \* \* \/etc\/init.d\/bluetooth restart/d" /var/spool/cron/root >/dev/null 2>&1

    echo
    echo "No Bluetooth battery configuration found in \"/data/etc/dbus-serialbattery/config.ini\"."
    echo "You can ignore this, if you are using only a serial connection."
    echo

fi
### BLUETOOTH PART | END ###



### CAN PART | START ###

# get CAN port(s) from config file
can_port=$(awk -F "=" '/^CAN_PORT/ {print $2}' /data/etc/dbus-serialbattery/config.ini)
#echo $can_port

# clear whitespaces
can_port_clean="$(echo $can_port | sed 's/\s*,\s*/,/g')"
#echo $can_port_clean

# split into array
IFS="," read -r -a can_array <<< "$can_port_clean"
#declare -p can_array
# readarray -td, can_array <<< "$can_port_clean,"; unset 'can_array[-1]'; declare -p can_array;

can_lenght=${#can_array[@]}
# echo $can_lenght

# stop all dbus-canbattery services, if at least one exists
if [ -d "/service/dbus-canbattery.0" ]; then
    svc -u /service/dbus-canbattery.*

    # always remove existing canbattery services to cleanup
    rm -rf /service/dbus-canbattery.*

    # kill all canbattery processes that remain
    pkill -f "supervise dbus-canbattery.*"
    pkill -f "multilog .* /var/log/dbus-canbattery.*"
    pkill -f "python .*/dbus-serialbattery.py .*_Ble"

    # kill opened bluetoothctl processes
    pkill -f "^bluetoothctl "
fi


if [ "$can_lenght" -gt 0 ]; then

    echo
    echo "Found $can_lenght CAN port(s) in the config file!"
    echo

    # install required packages
    # TO DO: Check first if packages are already installed
    echo "Installing required packages to use CAN connection..."

    opkg update
    opkg install python3-misc python3-pip

    echo
    pip3 install python-can

    echo "done."
    echo

    # function to install can battery
    install_canbattery_service() {
        if [ -z "$1" ]; then
            echo "ERROR: CAN port is empty. Aborting installation."
            echo
            exit 1
        fi
        #if [ -z "$2" ]; then
        #    echo "ERROR: BMS type for can port $1 is empty. Aborting installation."
        #    echo
        #    exit 1
        #fi

        echo "Installing CAN port \"$1\" as dbus-canbattery.$1"

        mkdir -p "/service/dbus-canbattery.$1/log"
        {
            echo "#!/bin/sh"
            echo "exec multilog t s25000 n4 /var/log/dbus-canbattery.$1"
        } > "/service/dbus-canbattery.$1/log/run"
        chmod 755 "/service/dbus-canbattery.$1/log/run"

        {
            echo "#!/bin/sh"
            echo "exec 2>&1"
            echo "echo"
            echo "python /opt/victronenergy/dbus-serialbattery/dbus-serialbattery.py $1"
        } > "/service/dbus-canbattery.$1/run"
        chmod 755 "/service/dbus-canbattery.$1/run"
    }

    # Example
    # install_canbattery_service can0
    # install_canbattery_service can9

    for (( i=0; i<can_lenght; i++ ));
    do
        # # split CAN port and BMS type
        # IFS=' ' read -r -a bms <<< "${can_array[$i]}"
        # install_canbattery_service $i "${bms[0]}" "${bms[1]}"
        install_canbattery_service "${can_array[$i]}"
    done

    # root@mutliplus-ii-gx:~# cansequence
    # interface = can0, family = 29, type = 3, proto = 1
    # write: No buffer space available

else

    echo
    echo "No CAN port configuration found in \"/data/etc/dbus-serialbattery/config.ini\"."
    echo "You can ignore this, if you are using only a serial connection."
    echo

fi
### CAN PART | END ###



### needed for upgrading from older versions | start ###
# remove old drivers before changing from dbus-blebattery-$1 to dbus-blebattery.$1
rm -rf /service/dbus-blebattery-*
# remove old install script from rc.local
sed -i "/^sh \/data\/etc\/dbus-serialbattery\/reinstalllocal.sh/d" /data/rc.local
sed -i "/^sh \/data\/etc\/dbus-serialbattery\/reinstall-local.sh/d" /data/rc.local
# remove old entry from rc.local
sed -i "/^sh \/data\/etc\/dbus-serialbattery\/installble.sh/d" /data/rc.local
### needed for upgrading from older versions | end ###



# install notes
echo
echo
echo "#################"
echo "# Install notes #"
echo "#################"
echo
echo "SERIAL battery connection: The installation is complete. You don't have to do anything more."
echo
echo "BLUETOOTH battery connection: There are a few more steps to complete installation."
echo
echo "    1. Please add the Bluetooth BMS to the config file \"/data/etc/dbus-serialbattery/config.ini\" by adding \"BLUETOOTH_BMS\" = "
echo "       Example with 1 BMS: BLUETOOTH_BMS = Jkbms_Ble C8:47:8C:00:00:00"
echo "       Example with 3 BMS: BLUETOOTH_BMS = Jkbms_Ble C8:47:8C:00:00:00, Jkbms_Ble C8:47:8C:00:00:11, Jkbms_Ble C8:47:8C:00:00:22"
echo "       If your Bluetooth BMS are nearby you can show the MAC address with \"bluetoothctl devices\"."
echo
echo "    2. Make sure to disable Bluetooth in \"Settings -> Bluetooth\" in the remote console/GUI to prevent reconnects every minute."
echo
echo "    3. Re-run \"/data/etc/dbus-serialbattery/reinstall-local.sh\", if the Bluetooth BMS were not added to the \"config.ini\" before."
echo
echo "    ATTENTION!"
echo "    If you changed the default connection PIN of your BMS, then you have to pair the BMS first using OS tools like the \"bluetoothctl\"."
echo "    See https://wiki.debian.org/BluetoothUser#Using_bluetoothctl for more details."
echo
echo "CAN battery connection: There are a few more steps to complete installation."
echo
echo "    1. Please add the CAN port to the config file \"/data/etc/dbus-serialbattery/config.ini\" by adding \"CAN_PORT\" = "
echo "       Example with 1 CAN port: CAN_PORT = can0"
echo "       Example with 3 CAN port: CAN_PORT = can0, can8, can9"
echo
echo "    2. Make sure to select a profile with 250 kbit/s in \"Settings -> Services -> VE.Can port -> CAN-bus profile\" in the remote console/GUI."
echo
echo "    3. Re-run \"/data/etc/dbus-serialbattery/reinstall-local.sh\", if the CAN port was not added to the \"config.ini\" before."
echo
echo "CUSTOM SETTINGS: If you want to add custom settings, then check the settings you want to change in \"/data/etc/dbus-serialbattery/config.default.ini\""
echo "                 and add them to \"/data/etc/dbus-serialbattery/config.ini\" to persist future driver updates."
echo
echo
