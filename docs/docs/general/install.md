---
id: install
title: How to install, update, disable, enable and uninstall
sidebar_position: 4
# Display h2 to h4 headings
toc_min_heading_level: 2
toc_max_heading_level: 4
---

# How to install, update, disable, enable and uninstall

## 🚨 NB! Before you begin

> The driver does not do any setup of your BMS/battery. You need to have a working battery before you start.

> It is always recommended to use the latest Venus OS version with the latest driver version. To avoid a [white screen](../faq/#fix-white-screen-after-install) after install check the compatibility matrix below.

> Multi battery setup: If you are using multiple batteries you need to use a battery aggregator else you cannot use the full system power. See [How to aggregate multiple batteries?](../faq/#how-to-aggregate-multiple-batteries)

## Compatibility Matrix

| &darr; Venus OS version \ Driver version &rarr;  | v0.12.0  | v0.13.0  | v0.14.x              | v1.0.0   |
| ---                                              | :---:    | :---:    | :---:                | :---:    |
| v2.80 - v2.84                                    | x        | x        | untested             | untested |
| v2.85 - v2.89                                    | x        | x        | untested             | untested |
| v2.90 - v2.94                                    | untested | x        | x                    | x        |
| v3.00~1 - v3.00~13                               | untested | untested | x                    | x        |
| v3.00~14 - v3.00~42                              | untested | untested | x<sup>1)</sup>       | x        |
| v3.00 - v3.20~30                                 | untested | untested | x<sup>1)</sup>       | x        |

1) Partially supported. Empty values/pages are not hidden in the GUI

## Default hard limits

The driver currently implement some hard limits. Make sure your device is set up correctly and can handle these limits before you install.

 * `50A` charge
 * `60A` discharge
 * `2.9V` min cell voltage
 * `3.45V` max cell voltage

The cell voltages is used along with the cell count to set the battery voltage (e.g. for 16 cells your battery min voltage will be `3.1 * 16 = 49.6V` and max coltage `3.45 * 16 = 55.2V`)

This limits can be changed in the settings. See [How to change the default limits](#how-to-change-the-default-limits) and [Settings location/path](#settings-locationpath).

## Settings for your BMS/battery

You need to first set up your BMS hardware to match your cells. You would do this, if you build you own battery or your manufacturer/installer have done this for you.
The important steps:

 * Use the same cells (type, branch and capacity) and make sure they are balanced.
 * You need to correctly set your battery capacity to match the cells you are using. Your SoC calculation in your BMS will be wrong otherwise. If you use `120Ah` cells then your battery capacity will be `120Ah` etc.
 * You need to correctly set your min/max cell protection voltages. These are voltages when your BMS will disconnect to protect your cells like `2.85V` and `3.65V`. Your driver limits should be between these and NOT the same.

## Settings for your GX device

1. You need to have a Venus OS device set up and running on your GX system (VenusGX, Cerbo, Raspberry Pi, etc.) and connected to your inverter.
In [VRM](https://vrm.victronenergy.com/) look under the device list for your installation. If you can see the Gateway (GX) and Ve.Bus System (inverter) then your GX is ready.

2. On your GX device you should set DVCC On. This will enable your battery to request charge parameters. All the Share Sense option can be Off. If your battery works with lower limits, enable Limit Charge Current, Limit managed battery Charge Voltage and set the lower values as required. You can also enable Limit inverter power for Discharge Current limit under ESS. These settings will be remembered between updates.
![DVCC values](../../screenshots/settings-dvcc.png)

3. You also need to connect your BMS to the Venus OS device using a serial interface. Use the cable for your BMS or a Victron branded USB&rarr;RS485 or USB&rarr;Ve.Direct (RS232) cable for best compatibility. Most FTDI/FT232R/CH340G USB&rarr;serial also works. The FT232R and CH340G already has a driver included in the Venus OS.

  > 🚨 **NB! Only connect Rx & Tx or A & B to the BMS,** if you are NOT using an isolated ([galvanic isolation](https://en.wikipedia.org/wiki/Galvanic_isolation)) cable or adapter. This prevents the current to flow through the adapter, if the BMS cuts the ground. Else it will destroy your BMS, GX device or Raspberry Pi.

## Install or update

### Installation video (`<= v0.14.3`)

[![dbus-serialbattery install](https://img.youtube.com/vi/Juht6XGLcu0/0.jpg)](https://www.youtube.com/watch?v=Juht6XGLcu0)

### Install automatically with USB/SD card

> It might be, that this doesn't work on older CerboGX devices. In this case use SSH option instead.

1. Download and copy the [latest release](https://github.com/Louisvdw/dbus-serialbattery/releases) `venus-data.tar.gz` to the root of a USB flash drive that is in FAT32 format (a SD card is also an option for GX devices, but not for Raspberry Pi).

2. OPTIONAL (`>= v1.0.0`): Create a `config.ini` file in the root of your USB flash drive with your custom settings. Put `[DEFAULT]` in the first line of the file and add all the values you want to change below. You only have to insert the values you want to change, all other values are fetched from the `config.default.ini`. In the [`config.default.ini`](https://github.com/Louisvdw/dbus-serialbattery/blob/master/etc/dbus-serialbattery/config.default.ini) you find all possible settings that you can copy over and change.

   > If you put a `config.ini` in the root of the USB flash drive, then an existing `config.ini` will be overwritten.

3. Plug the flash drive/SD into the Venus device and reboot. It will automatically extract and install to the correct locations and try the driver on any connected devices.

4. Reboot the GX (in the Remote Console go to `Settings` &rarr; `General` &rarr; `Reboot?`).


### Install over SSH

> Require [root access](https://www.victronenergy.com/live/ccgx:root_access#root_access)

1. Log into your Venus OS device using a SSH client like [Putty](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html) or bash.

2. Run these commands to start the installer. You can then choos, if you want to install the [latest release (recommended)](#latest-release-recommended), a [specific version](#specific-versiontroubleshooting-option), the [nightly build](#nightly-build) (from `master` or `dev`), a [local tar file](#local-tar-file) or quit.

  ```bash
  wget -O /tmp/install.sh https://raw.githubusercontent.com/Louisvdw/dbus-serialbattery/master/etc/dbus-serialbattery/install.sh

  bash /tmp/install.sh
  ```

#### Latest release (recommended)

Run the [install script ](../general/install#install-over-ssh) and select `1`.

💡 Reboot the system after the installation finished with `reboot`.

#### Specific version/troubleshooting option

Run the [install script ](../general/install#install-over-ssh) and select `2`. Go to [releases](https://github.com/Louisvdw/dbus-serialbattery/releases) and copy the link to the `venus-data.tar.gz` version you like to install. Paste the link with a right click and press enter.

💡 Reboot the system after the installation finished with `reboot`.

#### Nightly build

> Not recommended in production environment, unless you know what you do. Testers are very welcome!

Run the [install script ](../general/install#install-over-ssh) and select `3`.

Then select `1` if you want to install from the `master` branch or select `2` if you want to install from the `dev` branch.

The `master` branch can be seen as alpha version prior a pre-release or release is created.

The `dev` branch can be seen as most recent version, but also as the most unstable.  It could be that everything works as expected, but it can also brick your system and you have to reinstall from zero.

💡 Reboot the system after the installation finished with `reboot`.

#### Local tar file

Place a `venus-data.tar.gz` file in the folder `/var/volatile/tmp/` by copying/uploading it. Run the [install script ](../general/install#install-over-ssh) and select `3`.

💡 Reboot the system after the installation finished with `reboot`.


### BMS specific settings

* Daly BMS &rarr; Check [Why is the battery current inverted?](../faq/#why-is-the-battery-current-inverted) and [Daly Lost Connection because of standby](https://github.com/Louisvdw/dbus-serialbattery/issues/731#issuecomment-1613580083)
* ECS BMS &rarr; Check [#254 ECS BMS (comment)](https://github.com/Louisvdw/dbus-serialbattery/issues/254#issuecomment-1275924313)
* MNB BMS &rarr; Check [MNB BMS setup](https://github.com/Louisvdw/dbus-serialbattery/issues/590)

Since driver version `>= v1.0.0` you can also get an overview of the BMS specific settings be checking the end of the [`config.default.ini`](https://github.com/Louisvdw/dbus-serialbattery/blob/master/etc/dbus-serialbattery/config.default.ini).

## How to change the default limits

The driver currently uses a fixed upper current limit for the BMS:

* `50A` charge
* `60A` discharge

Should you require more current and your battery can handle that, than you can change it in the settings. The values to change are:

```ini
MAX_BATTERY_CHARGE_CURRENT = 50.0
MAX_BATTERY_DISCHARGE_CURRENT = 60.0
```

See [Settings location/path](#settings-locationpath).

If you use the cell voltage limits, temperature limits and/or SoC limits you also need to adjust their values to match the new current, else CCL and DCL will not change. See also [Why is the charging/discharging current limit (CCL/DCL) smaller than the set one?](../faq/#why-is-the-chargingdischarging-current-limit-ccldcl-smaller-than-the-set-one).

## Settings location/path

💡 After updating the settings reboot the device or run `/data/etc/dbus-serialbattery/reinstall-local.sh` to apply the changes.

The path of the settings file depends on you driver version. If you don't know which driver version you have installed see [Which version do I have installed?](../faq/#which-version-do-i-have-installed)

### Driver version `<= v0.14.3` (`utils.py`)
Edit `/data/etc/dbus-serialbattery/utils.py` to update the constants. Note that any updates will override this change.

### Driver version `>= v1.0.0` (`config.ini`)
Copy the values you want to change from `/data/etc/dbus-serialbattery/config.default.ini` and insert in the `/data/etc/dbus-serialbattery/config.ini`.

All available options can also be found [here](https://github.com/Louisvdw/dbus-serialbattery/blob/master/etc/dbus-serialbattery/config.default.ini).

## How to edit `utils.py` or `config.ini`

There are two ways to edit the files. You can edit them:

1. Inside the GX device/Raspberry Pi over SSH
2. On your PC and then copy only the `utils.py` or `config.ini` over to the GX device/Raspberry Pi

### SSH edit using Nano editor (recommended)

Log into your GX device/Raspberry Pi using SSH and run this command. Replace `FILE_NAME` with the file name you want to edit.

```bash
nano /data/etc/dbus-serialbattery/FILE_NAME
```

You can use the arrow keys to scroll down and edit the values you need.

Use `Ctrl + O` (O like Oskar) to save and `Ctrl + X` to exit the editor.

### Copy edited file from PC to GX device/Raspberry Pi

You can edit the file in a plain text editor on you PC like Notepad (Windows) or TextEdit (macOS). Then you need a program that can do SFTP like [FileZilla](https://filezilla-project.org/download.php?show_all=1) (Windows/macOS/Linux), [WinSCP](https://winscp.net/eng/downloads.php) (Windows) or [Cyberduck](https://cyberduck.io/download/) (macOS).

Connect to your GX using the same login as with SSH and copy your edited file over the existing one at `/data/etc/dbus-serialbattery/utils.py` or `/data/etc/dbus-serialbattery/config.ini`.

⚠️ Sometimes it happens, that the line endings get changed from `LF` to `CRLF` with this method. Check the [FAQ --> `$'\r': command not found` or `syntax error: unexpected end of file`](../faq/#r-command-not-found-or-syntax-error-unexpected-end-of-file) to solve.

> Don't copy all the files as the required file permissions will be destroyed and your driver might fail to start.

## How to enable a disabled BMS
If your BMS is disabled by default, you have to enable it to get it working.

💡 See also [How to edit `utils.py` or `config.ini`](#how-to-edit-utilspy-or-configini) if you don't know how to edit a file.

#### Driver version `<= v0.14.3`
Edit `/data/etc/dbus-serialbattery/utils.py` and uncomment (remove the `#` as first line character) your BMS.

E.g.

```python
#    {"bms" : "Sinowealth"},
```
becomes

```python
    {"bms" : "Sinowealth"},
```

Edit `/data/etc/dbus-serialbattery/dbus-serialbattery.py` and check, if your BMS is already uncommented (without the `#` as first line character) your BMS.

#### Driver version `>= v1.0.0` and `<= v1.0.20230610beta`
Edit `/data/etc/dbus-serialbattery/dbus-serialbattery.py` and uncommented (without the `#` as first line character) your BMS twice (`# from ...` and `# {"bms": ...}`).

#### Driver version `>= v1.0.20230611beta`
Add your BMS to the setting `BMS_TYPE` in the `config.ini`. This way you don't have to enable your BMS after every update.


## Disable the driver
You can disable the driver so that it will not be run by the GX device. To do that run the following command in SSH.

```bash
bash /data/etc/dbus-serialbattery/disable.sh
```

You also need to configure your MPPTs to run in `Stand alone mode` again. Follow the Victron guide for [Err 67 - BMS Connection lost](https://www.victronenergy.com/live/mppt-error-codes#err_67_-_bms_connection_lost).

## Enable the driver
To enable the driver again you can run the installer.

```bash
bash /data/etc/dbus-serialbattery/reinstall-local.sh
```

## Uninstall/remove the driver

To uninstall the driver run the uninstall script. The script is included from driver version `>= v1.0.0`.

```bash
bash /data/etc/dbus-serialbattery/uninstall.sh
```

To uninstall previous driver versions `<= v0.14.3` run this commands:

**Uninstall**

```bash
# handle read only mounts
sh /opt/victronenergy/swupdate-scripts/remount-rw.sh

# remove files, don't use variables here, since on an error the whole /opt/victronenergy gets deleted
rm -rf /data/conf/serial-starter.d
rm -rf /opt/victronenergy/service/dbus-serialbattery
rm -rf /opt/victronenergy/service-templates/dbus-serialbattery
rm -rf /opt/victronenergy/dbus-serialbattery

# kill driver, if running
pkill -f "python .*/dbus-serialbattery.py"

# remove install script from rc.local
sed -i "/sh \/data\/etc\/dbus-serialbattery\/reinstalllocal.sh/d" /data/rc.local

# restore GUI changes
bash /data/etc/dbus-serialbattery/restore-gui.sh
```

> If after the uninstall for some reason several items in the GUI were red, DO NOT reboot your GX device. See [Uninstalling driver bricked my cerbo #576](https://github.com/Louisvdw/dbus-serialbattery/issues/576)

**Remove**

If you want to remove also the install files of the driver run this after you run the uninstall script/commands:

```bash
rm -rf /data/etc/dbus-serialbattery
```


## Downgrade from `>= v1.0.0` to `<= v0.14.3`

With `>= v1.0.0` the serial starter config is created differently and therefore you have to delete the `/data/conf/serial-starter.d` folder before downgrading to `<= v0.14.3`, else you will get an error like this during installation of `<= v0.14.3`:

```bash
tar: conf/serial-starter.d: Cannot open: File exists
tar: Exiting with failure status due to previous errors
```

To solve this proble run

```bash
rm -rf /data/conf/serial-starter.d
```

before the install script.
