#!/bin/bash

# remove comment for easier troubleshooting
#set -x

PS3="Select the branch you want to install the unreleased code (possible bugs included): "

select branch in master jkbms_ble quit
do
    case $branch in
        master)
            echo "Selected branch: $branch"
            #echo "Selected number: $REPLY"
            break
            ;;
        jkbms_ble)
            echo "Selected branch: $branch"
            #echo "Selected number: $REPLY"
            break
            ;;
        quit)
            exit 0
            ;;
        *)
            echo "Invalid option $REPLY"
            ;;
    esac
done


cd /tmp

wget https://github.com/Louisvdw/dbus-serialbattery/archive/refs/heads/$branch.zip
unzip $branch.zip

cp -rf /tmp/dbus-serialbattery-$branch/etc/dbus-serialbattery/ /data/etc

chmod +x /data/etc/dbus-serialbattery/*.sh
chmod +x /data/etc/dbus-serialbattery/*.py
chmod +x /data/etc/dbus-serialbattery/service/run
chmod +x /data/etc/dbus-serialbattery/service/log/run

bash /data/etc/dbus-serialbattery/reinstalllocal.sh

if [[ $branch == "jkbms_ble" ]]; then
    nano /data/etc/dbus-serialbattery/installble.sh
fi
