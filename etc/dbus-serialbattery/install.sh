#!/bin/bash

# remove comment for easier troubleshooting
#set -x


# check if at least 5 MB free space is available on the system partition
freeSpace=$(df -m /data | awk 'NR==2 {print $4}')
if [ $freeSpace -lt 5 ]; then
    echo
    echo
    echo "ERROR: Not enough free space on the data partition. At least 5 MB are required."
    echo
    echo "       Please free up some space and try again."
    echo
    echo
    exit 1
fi


echo
# fetch version numbers for different versions
echo -n "Fetch current version numbers..."

# mr-manuel stable
latest_release_mrmanuel_stable=$(curl -s https://api.github.com/repos/mr-manuel/venus-os_dbus-serialbattery/releases/latest | grep "tag_name" | cut -d : -f 2,3 | tr -d "\ " | tr -d \" | tr -d \,)

# mr-manuel beta
latest_release_mrmanuel_beta=$(curl -s https://api.github.com/repos/mr-manuel/venus-os_dbus-serialbattery/releases | grep "tag_name.*beta" | cut -d : -f 2,3 | tr -d "\ " | tr -d \" | tr -d \, | head -n 1)

# mr-manuel master branch
latest_release_mrmanuel_nightly=$(curl -s https://raw.githubusercontent.com/mr-manuel/venus-os_dbus-serialbattery/master/etc/dbus-serialbattery/utils.py | grep DRIVER_VERSION | awk -F'"' '{print "v" $2}')

# done
echo " done."



# show current installed version
if [ -f "/data/etc/dbus-serialbattery/utils.py" ]; then
    current_version=$(grep DRIVER_VERSION /data/etc/dbus-serialbattery/utils.py | awk -F'"' '{print $2}')
    echo
    echo "** Currently installed version: v$current_version **"
fi



echo
PS3=$'\nSelect which version you want to install and enter the corresponding number: '

# create list of versions
version_list=(
    "latest release \"$latest_release_mrmanuel_stable\" (mr-manuel's repo, stable, most up to date)"
    "beta build \"$latest_release_mrmanuel_beta\" (mr-manuel's repo, no errors after 72 h runtime, long time testing needed)"
    "nightly build \"$latest_release_mrmanuel_nightly\" (mr-manuel's repo, newest features and fixes, bugs possible)"
    "specific branch (mr-manuel's repo, specific feature testing)"
    "specific version"
    "local tar file"
    "quit"
)

select version in "${version_list[@]}"
do
    case $version in
        "latest release \"$latest_release_mrmanuel_stable\" (mr-manuel's repo, stable, most up to date)")
            break
            ;;
        "beta build \"$latest_release_mrmanuel_beta\" (mr-manuel's repo, no errors after 72 h runtime, long time testing needed)")
            break
            ;;
        "nightly build \"$latest_release_mrmanuel_nightly\" (mr-manuel's repo, newest features and fixes, bugs possible)")
            break
            ;;
        "specific branch (mr-manuel's repo, specific feature testing)")
            break
            ;;
        "specific version")
            break
            ;;
        "local tar file")
            break
            ;;
        "quit")
            exit 0
            ;;
        *)
            echo "> Invalid option: $REPLY. Please enter a number!"
            ;;
    esac
done

echo "> Selected: $version"
echo ""



## latest release (mr-manuel, most up to date)
if [ "$version" = "latest release \"$latest_release_mrmanuel_stable\" (mr-manuel's repo, stable, most up to date)" ]; then
    # download latest release
    curl -s https://api.github.com/repos/mr-manuel/venus-os_dbus-serialbattery/releases/latest | grep "browser_download_url.*gz" | cut -d : -f 2,3 | tr -d \" | wget -O /tmp/venus-data.tar.gz -qi -
fi

## beta release (mr-manuel, most up to date)
if [ "$version" = "beta build \"$latest_release_mrmanuel_beta\" (mr-manuel's repo, no errors after 72 h runtime, long time testing needed)" ]; then
    # download beta release
    curl -s https://api.github.com/repos/mr-manuel/venus-os_dbus-serialbattery/releases/tags/$latest_release_mrmanuel_beta | grep "browser_download_url.*gz" | cut -d : -f 2,3 | tr -d \" | wget -O /tmp/venus-data.tar.gz -qi -
fi

## specific version
if [ "$version" = "specific version" ]; then
    # read the url
    read -r -p "Enter the url of the \"venus-data.tar.gz\" you want to install: " tar_url
    wget -O /tmp/venus-data.tar.gz "$tar_url"
    if [ $? -ne 0 ]; then
        echo "Error during downloading the TAR file. Please check, if the URL is correct."
        exit
    fi
fi

## local tar file
if [ "$version" = "local tar file" ]; then
    echo "Make sure the file is available at \"/var/volatile/tmp/venus-data.tar.gz\""
fi

# backup config.ini
if [ -f "/data/etc/dbus-serialbattery/config.ini" ]; then
    mv /data/etc/dbus-serialbattery/config.ini /data/etc/dbus-serialbattery_config.ini.backup
fi



## extract the tar file
if [ "$version" = "latest release \"$latest_release_mrmanuel_stable\" (mr-manuel's repo, stable, most up to date)" ] || [ "$version" = "beta build \"$latest_release_mrmanuel_beta\" (mr-manuel's repo, no errors after 72 h runtime, long time testing needed)" ] || [ "$version" = "specific version" ] || [ "$version" = "local tar file" ]; then

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



## nightly builds
if [ "$version" = "nightly build \"$latest_release_mrmanuel_nightly\" (mr-manuel's repo, newest features and fixes, bugs possible)" ] || [ "$version" = "specific branch (mr-manuel's repo, specific feature testing)" ]; then

    cd /tmp

    if [ "$version" = "specific branch (mr-manuel's repo, specific feature testing)" ]; then

        # fetch branches from Github
        branches=$(curl -s https://api.github.com/repos/mr-manuel/venus-os_dbus-serialbattery/branches | grep "name" | cut -d : -f 2,3 | tr -d \" | tr -d \, | grep -v "docusaurus")

        # create a select menu
        echo
        PS3=$'\nSelect the branch you want to install and enter the corresponding number: '

        select branch in $branches
        do
            if [[ -z "$branch" ]]; then
                echo "> Invalid selection. Please try again."
            else
                break
            fi
        done

        echo "> Selected branch: $branch"

    else

        branch="master"

    fi

    # clean already extracted folder
    rm -rf /tmp/venus-os_dbus-serialbattery-$branch

    # download driver
    wget -O $branch.zip https://github.com/mr-manuel/venus-os_dbus-serialbattery/archive/refs/heads/$branch.zip
    if [ $? -ne 0 ]; then
        echo "Error during downloading the ZIP file. Please try again."
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
    cp -rf /tmp/venus-os_dbus-serialbattery-$branch/etc/dbus-serialbattery/ /data/etc

    # set permissions
    chmod +x /data/etc/dbus-serialbattery/*.sh
    chmod +x /data/etc/dbus-serialbattery/*.py
    chmod +x /data/etc/dbus-serialbattery/service/run
    chmod +x /data/etc/dbus-serialbattery/service/log/run

fi


# fix owner and group
chown -R root:root /data/etc/dbus-serialbattery


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
