---
id: troubleshoot
title: How to troubleshoot
sidebar_position: 2
# Display h2 to h4 headings
toc_min_heading_level: 2
toc_max_heading_level: 4
---

# How to troubleshoot

## Driver log files

> Require [root access](https://www.victronenergy.com/live/ccgx:root_access#root_access)

Check the log files on your GX device/Raspberry Pi. Connect to your Venus OS device using a SSH client like [Putty](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html) or bash.


### Serial BMS connection

#### `/data/log/serial-starter/current`

Serial starter will show, if the driver was started against a USB port.

**Execute**
```bash
tail -n 100 -f /data/log/serial-starter/current | grep dbus-serialbattery | tai64nlocal
```

**Output**
```bash
...
INFO: Create daemontools service dbus-serialbattery.ttyUSB0
INFO: Start service dbus-serialbattery.ttyUSB0 once
...
```

✅ This indicates, that the driver was successfully started against the `USB0` port.

#### `/data/log/dbus-serialbattery.ttyUSB*/current` or `/data/log/dbus-serialbattery.ttyAMA0/current`
Where `*` is the number of your USB port (e.g. `ttyUSB0`, `ttyUSB1`, `ttyUSB2`, ...) or `ttyAMA0`, if you are using a Raspberry Pi hat.

**Execute**
```bash
tail -n 100 -f /data/log/dbus-serialbattery.ttyUSB0/current | tai64nlocal
```

**Output**
```bash
...
INFO:SerialBattery:Starting dbus-serialbattery
INFO:SerialBattery:dbus-serialbattery v1.0.0
INFO:SerialBattery:Testing BMS_NAME
...
INFO:SerialBattery:Connection established to BMS_NAME
INFO:SerialBattery:Battery BMS_NAME connected to dbus from /dev/ttyUSB0
...
INFO:SerialBattery:DeviceInstance = 1
INFO:SerialBattery:com.victronenergy.battery.ttyUSB0
...
```
✅ This indicates, that your driver started successfully and connected to your BMS. You can see now the BMS in the GUI.

❌ If you see an error like below, then your battery is most likely connected to a different `ttyUSB` port.

```bash
ERROR:SerialBattery:ERROR >>> No battery connection at /dev/ttyUSB0
```


### Bluetooth BMS connection

#### `/data/log/dbus-blebattery.*/current`
When you are using a Bluetooth connection `*` is the MAC address of your BMS.

**Execute**
```bash
tail -n 100 -f /data/log/dbus-blebattery.*/current | tai64nlocal
```

**Output**
```bash
...
INFO:SerialBattery:dbus-serialbattery v1.0.0
INFO:SerialBattery:init of BMS_NAME at BMS_MAC_ADDRESS
INFO:SerialBattery:test of BMS_NAME at BMS_MAC_ADDRESS
INFO:SerialBattery:BMS_NAME found!
INFO:SerialBattery:Connection established to BMS_NAME
INFO:SerialBattery:Battery BMS_NAME connected to dbus from BMS_MAC_ADDRESS
...
INFO:SerialBattery:DeviceInstance = 1
INFO:SerialBattery:com.victronenergy.battery.BMS_MAC_ADDRESS
...
```
✅ This indicates, that your driver started successfully and connected to your BMS. You can see now the BMS in the GUI.

❌ If you see an error like below, then your battery is not found.

```bash
INFO:SerialBattery:Starting dbus-serialbattery
INFO:SerialBattery:dbus-serialbattery v1.0.0
INFO:SerialBattery:init of BMS_NAME at BMS_MAC_ADDRESS
INFO:SerialBattery:test of BMS_NAME at BMS_MAC_ADDRESS
ERROR:SerialBattery:no BMS found at BMS_MAC_ADDRESS
ERROR:SerialBattery:ERROR >>> No battery connection at BMS_NAME
```


### What to check, if it doesn't work

The log file will tell you what the driver did and where it failed.


#### No log file
If there is no log folder under `/data/log/dbus-serialbattery.*` then check:

   * Did the install have any error? Reinstall the driver, also trying an alternative method.

   * Is the connection picked up by serial-starter? Use the command

     ```bash
     tail -f /data/log/serial-starter/current | tai64nlocal
     ```

     to show the last part of the log file as it updates. Plug your USB device in and out to see, if it's picked up and what `tty` port it uses.

   * Check, if your BMS type is found (change to the `ttyUSB*` your device use)

     ```bash
     tail -f /data/log/dbus-serialbattery.ttyUSB0/current | tai64nlocal
     ```

     or

     ```bash
     tail -f /data/log/dbus-serialbattery.*/current | tai64nlocal
     ```

     to check all devices the serialstarter started.

#### `No reply` in log file

Check your cable connections, if the log file shows `ERROR: No reply - returning` from the battery.

The RX/TX lights should both flash as data is transfered. If only one flashes then your RX/TX might be swapped.

## FAQ (Frequently Asked Questions)

Check the [FAQ (Frequently Asked Questions)](../faq) for answers

## Alarm logs (VRM Portal)

Check your Alarm Logs in your [VRM portal](https://vrm.victronenergy.com/installation-overview) after selecting your device.

## Advanced section (VRM Portal)

Check your graphs in Advanced section in your [VRM Portal](https://vrm.victronenergy.com/installation-overview) after selectiong your device.

You can use the graphs to look at your values over time. This makes finding values that change much easier.

* Battery SOC (State Of Charge)
* Battery Summary
* Battery Temperature Sensor
* Battery Voltage and Current
* BMS Charge and Discharge Limits
* BMS Min/Max Cell Voltage


## Forum and community help

Forum thead discussions for this driver can be found at:

* [GitHub Discussions](https://github.com/Louisvdw/dbus-serialbattery/discussions) (most frequented and recommended)
* [Energy Talk - DIY Serial battery driver for Victron GX](https://energytalk.co.za/t/diy-serial-battery-driver-for-victron-gx/80)
* [Victron Community - Victron VenusOS driver for serial battery BMS](https://community.victronenergy.com/questions/76159/victron-venusos-driver-for-serial-connected-bms-av.html)
* [DIY Solar Power Forum - Victron VenusOS driver for serial connected BMS](https://diysolarforum.com/threads/victron-venusos-driver-for-serial-connected-bms-available-ltt-power-jbd-battery-overkill-solar-smart-bms.17847/)
