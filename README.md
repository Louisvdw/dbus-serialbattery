# dbus-serialbattery
This is a driver for VenusOS devices (any GX device sold by Victron or a Raspberry Pi running the VenusOS image).

The driver will communicate with a Battery Management System (BMS) that support serial communication (RS232, RS485 or TTL UART) and publish this data to the VenusOS system. The main purpose is to act as a Battery Monitor in your GX and supply State of Charge (SoC) and other values to the inverter.

## Documentation
Check the documenation for more informations.
* [Introduction](https://louisvdw.github.io/dbus-serialbattery/)
  * [Features](https://louisvdw.github.io/dbus-serialbattery/general/features)
  * [Supported BMS](https://louisvdw.github.io/dbus-serialbattery/general/supported-bms)
  * [How to install](https://louisvdw.github.io/dbus-serialbattery/general/install)
* [Troubleshoot](https://louisvdw.github.io/dbus-serialbattery/troubleshoot/)
  * [FAQ (Frequently Asked Questions)](https://louisvdw.github.io/dbus-serialbattery/troubleshoot/faq)

## Supporting this project:
If you find this driver helpful please considder supporting this project. You can buy me a Ko-Fi or get in contact if you would like to donate hardware.

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/Z8Z73LCW1) or using [Paypal.me](https://paypal.me/innernet)

## Developer Remarks
To develop this project, install the requirements. This project makes use of velib_python which is pre-installed on
Venus OS Devices under `/opt/victronenergy/dbus-systemcalc-py/ext/velib_python`. To use the python files locally,
`git clone` the [velib_python](https://github.com/victronenergy/velib_python) project to velib_python and add
velib_python to the `PYTHONPATH` environment variable.

## How it works
* Each supported BMS needs to implement the abstract base class `Battery` from `battery.py`.
* `dbus-serialbattery.py` tries to figure out the correct connected BMS by looping through all known implementations of
`Battery` and executing its `test_connection()`. If this returns true, `dbus-serialbattery.py` sticks with this battery
and then periodically executes `dbushelper.publish_battery()`. `publish_battery()` executes `Battery.refresh_data()` which
updates the fields of Battery. It then publishes those fields to dbus using `dbushelper.publish_dbus()`
* The Victron Device will be "controlled" by the values published on `/Info/` - namely:
  * `/Info/MaxChargeCurrent `
  * `/Info/MaxDischargeCurrent`
  * `/Info/MaxChargeVoltage`
  * `/Info/BatteryLowVoltage` (note that Low Voltage is ignored by the system)
  * `/Info/ChargeRequest` (not implemented in dbus-serialbattery)

For more details on the Victron dbus interface see [the official Victron dbus documentation](https://github.com/victronenergy/venus/wiki/dbus).
