---
id: troubleshoot
title: Troubleshoot
---

# Troubleshoot
### Check the [FAQ](https://github.com/Louisvdw/dbus-serialbattery/wiki/FAQ) for answers
### Check your Alarm Logs in your [VRM](https://vrm.victronenergy.com/)
### Check your graphs in Advance section in your [VRM](https://vrm.victronenergy.com/)
You can use the graphs to look at your values over time. This makes finding values that change much easier.
* BMS Charge and Dischare limits
* BMS Min/Max Cell Voltage
* Battery Voltage
* Battery Summary
### Check your cable connections if the log, file shows to reply from the battery.
The RX/TX lights should both flash as data is transfered. If only one flash then your RX/TX might be swopped.
### Check the log files on your GX device
There are 2 important log files on the Venus OS device to look at.
* `/data/log/serial-starter/current`
  - serial starter will show if the driver was started against a USB port. In this case USB0.
    ```
    Create daemontools service dbus-serialbattery.ttyUSB0

    Start service dbus-serialbattery.ttyUSB0 once
    ```

* `/data/log/dbus-serialbattery.ttyUSB0/current` where `ttyUSB0` will be your USB port (`ttyUSB0`/`ttyUSB1`/`ttyUSB2`/etc.) or `ttyAMA0`, if you are using a Raspberry Pi hat.
    ```
    INFO:__main__:dbus-serialbattery

    INFO:__main__:Battery connected to dbus from /dev/ttyUSB0
    ```

    If you see an error like below your battery is most likely connecting using a different ttyUSB port
    ```
    ERROR:__main__:ERROR >>> No battery connection at /dev/ttyUSB3
    ```

The log file will tell you what the driver did and where it failed.
If there is no log folder under `/data/log/dbus-serialbattery.*` then check
   - Did the install have any error. Reinstall the driver, also trying an alternative method.
   - Is the connection picked up by serial-starter? Use the command
     ```
     tail -f /data/log/serial-starter/current | tai64nlocal
     ```
     to show the last part of the log file as it updates, and plug your USB device in and out to see, if it is picked up and what tty port it uses.
   - Check, if your BMS type is found (change to the ttyUSB* your device use)
     ```bash
     tail -f /data/log/dbus-serialbattery.ttyUSB0/current | tai64nlocal
     ```
     or
     ```bash
     tail -f /data/log/dbus-serialbattery.*/current | tai64nlocal
     ```
     to check all devices the serialstarter started.


### Forum help
Forum thead discussions for this driver can be found at:
* https://github.com/Louisvdw/dbus-serialbattery/discussions (primary)
* https://energytalk.co.za/t/diy-serial-battery-driver-for-victron-gx/80
* https://community.victronenergy.com/questions/76159/victron-venusos-driver-for-serial-connected-bms-av.html
* https://diysolarforum.com/threads/victron-venusos-driver-for-serial-connected-bms-available-ltt-power-jbd-battery-overkill-solar-smart-bms.17847/
