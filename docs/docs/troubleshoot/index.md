---
id: troubleshoot
title: How to troubleshoot
sidebar_position: 2
# Display h2 to h4 headings
toc_min_heading_level: 2
toc_max_heading_level: 4
---

<!-- redirect to new documentation -->
<head>
  <meta http-equiv="refresh" content="1; url=https://mr-manuel.github.io/venus-os_dbus-serialbattery/troubleshoot" />
  <link rel="canonical" href="https://mr-manuel.github.io/venus-os_dbus-serialbattery/troubleshoot" />
</head>

# How to troubleshoot


## 🚨 IMPORTANT 🚨

* If you think it could be a bug and you did not already tested the `nightly` build, then install it and see if the error persists. See [here](../general/install.md#nightly-build) how to install it.

* If the logs don't give you enough valuable data, then change the logging from `INFO` to `DEBUG` in the config file. See [here](../general/install.md#how-to-edit-utilspy-or-configini) how to edit the `config.ini`.


## How the driver works

1. During installation (`execution of reinstall-local.sh`) the installer script creates a configuration file (`/data/conf/serial-starter.d/dbus-serialbattery.conf`) for the `serial starter`.
    This allows the `serial starter` to create services for `dbus-serialbattery`, if a new serial adapter is connected. The `serial starter` service (`/service/serial-starter`) then creates a
    service (`/service/dbus-serialbattery.*`) for each found serial port.

    Additionally during installation a service (`/service/dbus-blebattery.*`) for each Bluetooth BMS and (`/service/dbus-canbattery.*`) for each CAN BMS is created.

2. Each created service in `/service/dbus-serialbattery.*`, `/service/dbus-blebattery.*` or `/service/dbus-canbattery.*` runs `/opt/victronenergy/dbus-serialbattery/start-serialbattery.sh *`.

   * For `dbus-serialbattery` the `*` stands for the serial port, e.g. the service `/service/dbus-serialbattery.ttyUSB0` runs `/opt/victronenergy/dbus-serialbattery/start-serialbattery.sh ttyUSB0`.

   * For `dbus-blebattery` the `*` stands for an incremental number, e.g. the service `/service/dbus-blebattery.0` runs `/opt/victronenergy/dbus-serialbattery/dbus-serialbattery.py Jkbms_Ble C8:47:8C:00:00:00`, where the BMS type `Jkbms_Ble` and the BMS Bluetooth MAC address `C8:47:8C:00:00:00` is fetched from the config file during installation.

   * For `dbus-canbattery` the `*` stands for the can port, e.g. the service `/service/dbus-canbattery.can0` runs `/opt/victronenergy/dbus-serialbattery/start-serialbattery.sh can0`, where the CAN port `can0` is fetched from the config file during installation.



## Driver log files

> Require [root access](https://www.victronenergy.com/live/ccgx:root_access#root_access)

> 💡 If you are opening an issue or posting your logs somewhere please make sure you execute the complete commands to get the logs, including `tai64nlocal`. Without readable timestamps we cannot help you.

Check the log files on your GX device/Raspberry Pi. Connect to your Venus OS device using a SSH client like [Putty](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html) or bash.


### Serial BMS connection

> There are two log files that are relevant for the serial connection. Please check both.

1. `/data/log/serial-starter/current`
2. `/data/log/dbus-serialbattery.ttyUSB*/current` or `/data/log/dbus-serialbattery.ttyAMA0/current`

#### `/data/log/serial-starter/current`

Serial starter will show, if the driver was started against a USB port.

**Execute**

💡 The `tail` command with the parameter `-F` does not quit automatically, since it waits for new log entries.
You can exit by pressing `CTRL + C`.

```bash
tail -F -n 100 /data/log/serial-starter/current | grep dbus-serialbattery | tai64nlocal
```

**Output**
```bash
...
INFO: Create daemontools service dbus-serialbattery.ttyUSB0
INFO: Start service dbus-serialbattery.ttyUSB0 once
...
```

✅ This indicates, that the driver was successfully started against the `USB0` port.

❌ If there is no `dbus-serialbattery.tty*` entry check with `lsusb`, if your USB to serial converter is recognized from Venus OS.

Here are some partial `lsusb` outputs which show a few different adapters. If you have attached only one adapter you will see only one similar entry as below:

`Bus 001 Device 002: ID 0403:6015 Future Technology Devices International, Ltd Bridge(I2C/SPI/UART/FIFO)`
`Bus 001 Device 003: ID 0403:6001 Future Technology Devices International, Ltd FT232 Serial (UART) IC`
`Bus 001 Device 004: ID 0403:6015 Future Technology Devices International, Ltd Bridge(I2C/SPI/UART/FIFO)`
`Bus 001 Device 005: ID 0403:6011 Future Technology Devices International, Ltd FT4232H Quad HS USB-UART/FIFO IC`
`Bus 002 Device 002: ID 1a86:7523 QinHeng Electronics HL-340 USB-Serial adapter`


#### `/data/log/dbus-serialbattery.ttyUSB*/current` or `/data/log/dbus-serialbattery.ttyAMA0/current`
Where `*` is the number of your USB port (e.g. `ttyUSB0`, `ttyUSB1`, `ttyUSB2`, ...) or `ttyAMA0`, if you are using a Raspberry Pi hat.

**Execute**

💡 The `tail` command with the parameter `-F` does not quit automatically, since it waits for new log entries.
You can exit by pressing `CTRL + C`.

```bash
tail -F -n 100 /data/log/dbus-serialbattery.ttyUSB0/current | tai64nlocal
```

**Output**
```bash
...
INFO:SerialBattery:Starting dbus-serialbattery
INFO:SerialBattery:Venus OS v3.40
INFO:SerialBattery:dbus-serialbattery v1.3.0
INFO:SerialBattery:-- Testing BMS: 1 of 3 rounds
INFO:SerialBattery:Testing BMS_NAME
...
INFO:SerialBattery:Connection established to BMS_NAME
INFO:SerialBattery:Battery BMS_NAME connected to dbus from /dev/ttyUSB0
...
INFO:SerialBattery:Serial Number/Unique Identifier: UNIQUE_IDENTIFIER
...
```
✅ This indicates, that your driver started successfully and connected to your BMS. You can see now the BMS in the GUI.

❌ If you see an error like below, then your battery is most likely connected to a different `ttyUSB` port.

```bash
ERROR:SerialBattery:ERROR >>> No battery connection at /dev/ttyUSB0
```


### Bluetooth BMS connection

#### `/data/log/dbus-blebattery.*/current`
Where `*` is an incremental number.

**Execute**

💡 The `tail` command with the parameter `-F` does not quit automatically, since it waits for new log entries.
You can exit by pressing `CTRL + C`.

```bash
tail -F -n 100 /data/log/dbus-blebattery.*/current | tai64nlocal
```

**Output**
```bash
...
INFO:SerialBattery:Starting dbus-serialbattery
INFO:SerialBattery:Venus OS v3.40
INFO:SerialBattery:dbus-serialbattery v1.3.0
INFO:SerialBattery:init of BMS_NAME at BMS_MAC_ADDRESS
INFO:SerialBattery:test of BMS_NAME at BMS_MAC_ADDRESS
INFO:SerialBattery:BMS_NAME found!
INFO:SerialBattery:Connection established to BMS_NAME
INFO:SerialBattery:Battery BMS_NAME connected to dbus from BMS_MAC_ADDRESS
...
INFO:SerialBattery:Serial Number/Unique Identifier: UNIQUE_IDENTIFIER
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


### CAN BMS connection

#### `/data/log/dbus-canbattery.*/current`
Where `*` is the number of your CAN port (e.g. `can0`, `can5`, `can9`, ...).

**Execute**

💡 The `tail` command with the parameter `-F` does not quit automatically, since it waits for new log entries.
You can exit by pressing `CTRL + C`.

```bash
tail -F -n 100 /data/log/dbus-canbattery.*/current | tai64nlocal
```

**Output**
```bash
...
INFO:SerialBattery:Starting dbus-serialbattery
INFO:SerialBattery:Venus OS v3.40
INFO:SerialBattery:dbus-serialbattery v1.3.0
INFO:SerialBattery:-- Testing BMS: 1 of 3 rounds
INFO:SerialBattery:Testing BMS_NAME
...
INFO:SerialBattery:Connection established to BMS_NAME
INFO:SerialBattery:Battery BMS_NAME connected to dbus from can0
...
INFO:SerialBattery:Serial Number/Unique Identifier: UNIQUE_IDENTIFIER
...
```
✅ This indicates, that your driver started successfully and connected to your BMS. You can see now the BMS in the GUI.

❌ If you see an error like below, then your battery is most likely connected to a different `can` port.

```bash
ERROR:SerialBattery:ERROR >>> No battery connection at can0
```


### What to check, if it doesn't work

The log file will tell you what the driver did and where it failed.


#### No log file
If there is no log folder under `/data/log/dbus-serialbattery.*` then check:

* Did the install have any error? Reinstall the driver, also trying an alternative method and version.

* Is the connection picked up by serial-starter?

  💡 The `tail` command with the parameter `-F` does not quit automatically, since it waits for new log entries.
  You can exit by pressing `CTRL + C`.

  Use the command

  ```bash
  tail -F /data/log/serial-starter/current | tai64nlocal
  ```

  to show the last part of the log file as it updates. Plug your USB device in and out to see, if it's picked up and what `ttyUSB` port it uses.

  You can also check, which USB port it used by plugging out your USB device, wait some seconds, execute the command below, plug in your USB device, execute the command below again and compare which `ttyUSB` device appeared now.

  **Execute**
  ```bash
  ls -l /dev/ttyUSB*
  ```

  **Example output (USB device unplugged)**
  ```bash
  crw-rw----    1 root     dialout   188,   0 Jun 11 17:08 /dev/ttyUSB0
  ```

  **Example output (USB device plugged)**
  ```bash
  crw-rw----    1 root     dialout   188,   0 Jun 11 17:08 /dev/ttyUSB0
  crw-rw----    1 root     dialout   188,   1 Jun 11 17:08 /dev/ttyUSB1
  ```

* Did the serial starter correctly assign the USB port to the correct service?

  If the content under `==> /data/var/lib/serial-starter/* <==` shows `sbattery` then this USB port is assigned to the `dbus-serialbattery` driver.

  **Execute**
  ```bash
  head /data/var/lib/serial-starter/*
  ```

  **Output**
  ```bash
  ==> /data/var/lib/serial-starter/ttyACM0 <==
  gps

  ==> /data/var/lib/serial-starter/ttyUSB0 <==
  vedirect

  ==> /data/var/lib/serial-starter/ttyUSB1 <==
  sbattery

  ==> /data/var/lib/serial-starter/ttyUSB2 <==
  vedirect
  ```

  If the assignment is wrong you can reset all executing this command

  ```bash
  rm /data/var/lib/serial-starter/*
  ```

  and then reboot. You can also overwrite an assignment by executing the command below.
  Change the `#` with the number of your USB port before executing the command. Reboot after the change.

  ```bash
  echo "sbattery" > /data/var/lib/serial-starter/ttyUSB#
  ```


* Check, if your BMS type is found (change to the `ttyUSB*` your device use)

  - For serial connected BMS

    💡 The `tail` command with the parameter `-F` does not quit automatically, since it waits for new log entries.
    You can exit by pressing `CTRL + C`.

    ```bash
    tail -F /data/log/dbus-serialbattery.ttyUSB0/current | tai64nlocal
    ```

    or

    ```bash
    tail -F /data/log/dbus-serialbattery.*/current | tai64nlocal
    ```

    to check all devices the serialstarter started.

  - For Bluetooth connected BMS

    💡 The `tail` command with the parameter `-F` does not quit automatically, since it waits for new log entries.
    You can exit by pressing `CTRL + C`.

    ```bash
    tail -F /data/log/dbus-blebattery.0/current | tai64nlocal
    ```

    or

    ```bash
    tail -F /data/log/dbus-blebattery.*/current | tai64nlocal
    ```

    to check all Bluetooth devices.



#### `No reply` in log file

Check your cable connections, if the log file shows `ERROR: No reply - returning` from the battery.

The RX/TX lights should both flash as data is transfered. If only one flashes then your RX/TX might be swapped.

#### Driver runtime (stability check)

Check for how long the driver is running without restart.

**Execute**

For serial connected BMS

```bash
svstat /service/dbus-serialbattery.tty*
```

For Bluetooth connected BMS

```bash
svstat /service/dbus-blebattery.*
```

**Output**
```bash
root@raspberrypi2:~# svstat /service/dbus-serialbattery.*
/service/dbus-serialbattery.ttyUSB0: up (pid 8136) 1128725 seconds
```
✅ If the seconds (`runtime`) have a high number (e.g. several days; 86400 seconds = 1 day) then this indicates, that your driver is stable.

❌ If the seconds (`runtime`) are low (e.g. 300 seconds) then this means your driver has (re)started 300 seconds ago.
Check again in a few minutes, if the `pid` changed and if the `runtime` increased or reset.
If that is the case, your driver is not stable and has a problem.

```bash
root@raspberrypi2:~# svstat /service/dbus-serialbattery.*
/service/dbus-serialbattery.ttyUSB0: up (pid 8136) 300 seconds
```

 Additionally you can check the system uptime.

 **Execute**
 ```bash
 uptime
 ```

**Output**
```bash
10:08:14 up 8 days,  3:24,  load average: 1.52, 0.87, 0.79
```



## FAQ (Frequently Asked Questions)

Check the [FAQ (Frequently Asked Questions)](../faq/index.md) for answers

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
