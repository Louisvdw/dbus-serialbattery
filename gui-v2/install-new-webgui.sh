#!/bin/bash

# change to /tmp directory
cd /tmp

# download the webassembly.zip file
wget -O /tmp/venus-webassembly.zip https://raw.githubusercontent.com/mr-manuel/venus-os_dbus-serialbattery/dev/gui-v2/venus-webassembly.zip

# unzip the file
unzip /tmp/venus-webassembly.zip

# remove the old webassembly directory
rm -rf /var/www/venus/gui-battery

# move the new webassembly directory to the correct location
mv /tmp/wasm /var/www/venus/gui-battery
