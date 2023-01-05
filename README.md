# dbus-serialbattery
This is a driver for VenusOS devices (any GX device sold by Victron or a Raspberry Pi running the VenusOS image). 

The driver will communicate with a Battery Management System (BMS) that support serial communication (RS232, RS485 or TTL UART) and publish this data to the VenusOS system. The main purpose is to act as a Battery Monitor in your GX and supply State Of Charge (SOC) and other values to the inverter.

 * [BMS Types supported](https://github.com/Louisvdw/dbus-serialbattery/wiki/BMS-types-supported)
 * [FAQ](https://github.com/Louisvdw/dbus-serialbattery/wiki/FAQ)
 * [Features](https://github.com/Louisvdw/dbus-serialbattery/wiki/Features)
 * [How to install](https://github.com/Louisvdw/dbus-serialbattery/wiki/How-to-install)
 * [Troubleshoot](https://github.com/Louisvdw/dbus-serialbattery/wiki/Troubleshoot)

### Supporting this project:
If you find this driver helpful please considder supporting this project. You can buy me a Ko-Fi or get in contact if you would like to donate hardware.

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/Z8Z73LCW1) or using [Paypal.me](https://paypal.me/innernet)

### Developer Remarks
To develop this project, install the requirements. This project makes use of velib_python which is pre-installed on 
Venus-OS Devices under `/opt/victronenergy/dbus-systemcalc-py/ext/velib_python`. To use the python files locally, 
`git clone` the [velib_python](https://github.com/victronenergy/velib_python) project to velib_python and add 
velib_python to the `PYTHONPATH` environment variable.