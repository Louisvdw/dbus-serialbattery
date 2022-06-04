# dbus-serialbattery
This is a driver for VenusOS devices (any GX device sold by Victron or a Raspberry Pi running the VenusOS image). 

The driver will communicate with a Battery Management System (BMS) that support serial communication (TTL, RS232 or RS485) 
Modbus RTU type commands and publish this data to the dbus used by VenusOS. The main purpose is to supply up to date 
State Of Charge (SOC), Voltage & Current values to the inverter so that your serial battery can be set as the Battery Monitor in the ESS settings. Many extra parameters and alarms are also published if available from the BMS.

 * [BMS Types supported](https://github.com/Louisvdw/dbus-serialbattery/wiki/BMS-types-supported)
 * [FAQ](https://github.com/Louisvdw/dbus-serialbattery/wiki/FAQ)
 * [Features](https://github.com/Louisvdw/dbus-serialbattery/wiki/Features)
 * [How to install](https://github.com/Louisvdw/dbus-serialbattery/wiki/How-to-install)
 * [Troubleshoot](https://github.com/Louisvdw/dbus-serialbattery/wiki/Troubleshoot)

### Donations:
If you would like to donate to this project, you can buy me a Ko-Fi. Get in contact if you would like to donate hardware.

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/Z8Z73LCW1) or using [Paypal.me](https://paypal.me/innernet)
