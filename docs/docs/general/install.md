---
id: install
title: How to install
---

## NB!! Before you begin
**The driver does not do any setup of your BMS/Battery. You need to have a working battery before you start**

**From release v0.12 you need to be running VenusOS firmware 2.80 or higher**
Note! The current version require firmware 2.91 or 2.92 or you will see a white screen after the install. I will remove this note when that issue is fixed.

The driver currently implement some hard limits. Make sure your device is set up correctly and can handle these limits before you install.
 * 50A charge (to lower this see 2. below Settings for your GX)
 * 60A discharge (to lower this see 2. below Settings for your GX)
 * 2.9V min cell voltage
 * 3.45V max cell voltage

The cell voltages is used along with the cell count to set the battery voltage(e.g. for 16cells your battery min voltage will be 3.1x16=49.6V and max coltage 3.45x16=55.2V

If you have other custom scripts installed, installing the driver might break that if they require /data/rc.local to work.

## Settings for your BMS/Battery
You need to first set up your BMS hardware to match your cells. You would do this if you build you own battery, or your manufacturer/installer have done this for you.
The important steps:
 * Use the same cells (type, branch and capacity) and make sure they are balanced.
 * You need to correctly set your battery capacity to match the cells you are using. Your SOC calculation in your BMS will be wrong otherwise. If you use 120Ah cells then your battery capacity will be 120Ah, etc.
 * You need to correctly set your min/max cell protection voltages. These are voltage when your BMS will disconnect to protect your cells like 2.85V and 3.65V. Your driver limits should be between these - not the same.

## Settings for your GX device
1. You need to have a VenusOS device set up and running on your GX system (VenusGX, Cerbo, Raspberry Pi, etc.) and connected to your inverter.
In [VRM](https://vrm.victronenergy.com/) look under the device list for your installation. If you can see the Gateway (GX) and Ve.Bus System (inverter) then your GX is ready.
2. On your GX device you should set DVCC On. This will enable your battery to request charge parameters. All the Share Sense option can be Off. If your battery works with lower limits, enable Limit Charge Current , Limit managed battery Charge Voltage and set the lower values as required. You can also enable Limit inverter power for Discharge Current limit under ESS. These settings will be remembered between updates.
![DVCC values](https://raw.githubusercontent.com/Louisvdw/dbus-serialbattery/master/images/DVCC.png)

3. You also need to connect your BMS to the VenusOS device using a serial interface. Use the cable for your BMS or a Victron branded USB->RS485 or USB->Ve.Direct(RS232) cable for best compatibility. Most FTDI/FT232R/CH340G USB->serial also works. The FT232R and CH340G already has a driver included in the VenusOS. **NB!  Only connect the Ground, Rx & Tx to the BMS** unless using an isolated cable.

## To install or Update
**CerboGX users cannot use the the Automatic installer. Use SSH option instead.**

### Installation video:
[![dbus-serialbattery install](https://img.youtube.com/vi/Juht6XGLcu0/0.jpg)](https://www.youtube.com/watch?v=Juht6XGLcu0)

### Automatic Installer option:
1. Download and copy the [latest release venus-data.tar.gz](https://github.com/Louisvdw/dbus-serialbattery/releases) to the root of a USB flash drive that is in Fat32 format. (A SD card is also an option for GX devices, but not for Raspberry Pi)
2. Plug the flash drive/SD into the Venus device and reboot. It will automatically extract and install to the correct locations and try the driver on any connected devices.
3. Reboot the GX (in Remote Console go to Settings -> General -> Reboot?)


### SSH installer script option:
**( Require [root access](https://www.victronenergy.com/live/ccgx:root_access) )**
1. Log into your VenusOS device using a SSH client like Putty or bash
2. Run these commands to install or update to the latest release version.
  > wget https://raw.githubusercontent.com/Louisvdw/dbus-serialbattery/master/etc/dbus-serialbattery/installrelease.sh

  > sh installrelease.sh

  > reboot


### install Spesific version/testing option:
**( Require [root access](https://www.victronenergy.com/live/ccgx:root_access) )**
1. Log into your VenusOS device using a SSH client like Putty or bash
2. Download the version you need using the command below replacing the URL with the link to the venus-data.tar.gz version you need
  > wget _**venus-data-URL**_
3. Run this script command to install the update from the same location
  > tar -zxf venus-data.tar.gz -C /data

  > reboot


### BMS specific settings
* ECS BMS --> https://github.com/Louisvdw/dbus-serialbattery/issues/254#issuecomment-1275924313



## Disable the driver

### Disable
You can disable the driver so that it will not be run by the GX device.
To do that run the following command in SSH.
 > sh /data/etc/dbus-serialbattery/disabledriver.sh

You also need to configure your MPPTs to run in Stand alone mode again. Follow the Victron guide for [Err 67 - BMS Connection lost](https://www.victronenergy.com/live/mppt-error-codes#err_67_-_bms_connection_lost).

### Enable
To enable the driver again you can run the installer
 > sh /data/etc/dbus-serialbattery/installrelease.sh

***


## How to increase the default limits
The driver currently use a fixed upper current limit for the BMS:
* 50A charge
* 60A discharge

If you require more current and your battery can handle that, you can make changes to the source code for that. (Note any updates will override this change)

Edit the source to update the constants.
/data/etc/dbus-serialbattery/utils.py

`MAX_BATTERY_CURRENT = 50.0`

`MAX_BATTERY_DISCHARGE_CURRENT = 60.0`

If you use the cell voltage limits or temperature limits you also need to adjust their values to match the new current

### How to edit utils.py
There are 2 ways to edit it.
You can edit it inside the GX while in SSH terminal
or edit it on your PC and then only copy the utils.py over to the GX.

#### SSH edit using Nano editor
Log into your GX using SSH and run `nano /data/etc/dbus-serialbattery/utils.py`
You can use the arrow keys to scroll down and edit the values you need.
User Ctrl-O to save and Ctrl-X to exit the editor, and reboot for the settings to apply.

#### Copy edited file from PC to GX device
You can edit the file in a plain text editor on you PC like notepad on Widows. Then you need a program that can do SFTP like FileZilla.
Connect to your GX using the same login as with SSH and copy your edited file over the existing one at `/data/etc/dbus-serialbattery/utils.py`
Don't copy all the files as the required file permissions will be destroyed and your driver might fail to start.
