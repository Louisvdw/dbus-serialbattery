#!/bin/bash

# remove comment for easier troubleshooting
#set -x

echo ""
PS3="Select which version you want to install and enter the corresponding number [1]: "

select version in "latest release (recommended)" "nightly build" "local tar file" "specific version" "quit"
do
    case $version in
        "latest release (recommended)")
            echo "Selected: $version"
            #echo "Selected number: $REPLY"
            break
            ;;
        "nightly build")
            echo "Selected: $version"
            #echo "Selected number: $REPLY"
            break
            ;;
        "local tar file")
            echo "Selected: $version"
            #echo "Selected number: $REPLY"
            break
            ;;
        "specific version")
            echo "Selected: $version"
            #echo "Selected number: $REPLY"
            break
            ;;
        "quit")
            exit 0
            ;;
        *)
            echo "Invalid option: $REPLY"
            echo "Please enter a number"
            ;;
    esac
done
echo ""

## latest release
if [ "$version" = "latest release (recommended)" ]; then
    # download latest release
    curl -s https://api.github.com/repos/Louisvdw/dbus-serialbattery/releases/latest | grep "browser_download_url.*gz" | cut -d : -f 2,3 | tr -d \" | wget -O /tmp/venus-data.tar.gz -qi -
fi

## local tar file
if [ "$version" = "local tar file" ]; then
    echo "Make sure the file is available at \"/var/volatile/tmp/venus-data.tar.gz\""
fi

## specific version
if [ "$version" = "specific version" ]; then
    # read the url
    read -p "Enter the url of the \"venus-data.tar.gz\" you want to install: " tar_url
    wget -O /tmp/venus-data.tar.gz $tar_url
    if [ $? -ne 0 ]; then
        echo "Error during downloading the TAR file. Please check, if the URL is correct."
        exit
    fi
fi



# backup config.ini
if [ -f "/data/etc/dbus-serialbattery/config.ini" ]; then
    mv /data/etc/dbus-serialbattery/config.ini /data/etc/dbus-serialbattery_config.ini.backup
fi



## extract the tar file
if [ "$version" = "latest release (recommended)" ] || [ "$version" = "local tar file" ] || [ "$version" = "specific version" ]; then

    # extract driver
    if [ -f "/tmp/venus-data.tar.gz" ]; then
        # remove old driver
        rm -rf /data/etc/dbus-serialbattery
        tar -zxf /tmp/venus-data.tar.gz -C /data
    else
        echo "There is no file in \"venus-data.tar.gz\""
        # restore config.ini
        if [ -f "/data/etc/dbus-serialbattery_config.ini.backup" ]; then
            mv /data/etc/dbus-serialbattery_config.ini.backup /data/etc/dbus-serialbattery/config.ini
        fi
        exit
    fi

fi


## nightly build
if [ "$version" = "nightly build" ]; then

    PS3="Select the branch from wich you want to install the current code (possible bugs included): "

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

    # clean already extracted folder
    rm -rf /tmp/dbus-serialbattery-$branch

    # download driver
    wget -O $branch.zip https://github.com/Louisvdw/dbus-serialbattery/archive/refs/heads/$branch.zip
    if [ $? -ne 0 ]; then
        echo "Error during downloading the TAR file. Please try again."
        # restore config.ini
        if [ -f "/data/etc/dbus-serialbattery_config.ini.backup" ]; then
            mv /data/etc/dbus-serialbattery_config.ini.backup /data/etc/dbus-serialbattery/config.ini
        fi
        exit
    fi

    # extract archive
    unzip -q $branch.zip

    # remove old driver
    rm -rf /data/etc/dbus-serialbattery

    # copy driver
    cp -rf /tmp/dbus-serialbattery-$branch/etc/dbus-serialbattery/ /data/etc

    # set permissions
    chmod +x /data/etc/dbus-serialbattery/*.sh
    chmod +x /data/etc/dbus-serialbattery/*.py
    chmod +x /data/etc/dbus-serialbattery/service/run
    chmod +x /data/etc/dbus-serialbattery/service/log/run

fi


# restore config.ini
if [ -f "/data/etc/dbus-serialbattery_config.ini.backup" ]; then
    mv /data/etc/dbus-serialbattery_config.ini.backup /data/etc/dbus-serialbattery/config.ini
fi


# run install script >= v1.0.0
if [ -f "/data/etc/dbus-serialbattery/reinstall-local.sh" ]; then
    bash /data/etc/dbus-serialbattery/reinstall-local.sh
# run install script < v1.0.0
elif [ -f "/data/etc/dbus-serialbattery/reinstalllocal.sh" ]; then
    bash /data/etc/dbus-serialbattery/reinstalllocal.sh
fi
