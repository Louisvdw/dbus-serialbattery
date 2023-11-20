# dbus-serialbattery
This is a driver for Venus OS devices (any GX device sold by Victron or a Raspberry Pi running the Venus OS image).

The driver will communicate with a Battery Management System (BMS) that support serial (RS232, RS485 or TTL UART) and Bluetooth communication (see [BMS feature comparison](https://louisvdw.github.io/dbus-serialbattery/general/features#bms-feature-comparison) for details). The data is then published to the Venus OS system (dbus). The main purpose is to act as a Battery Monitor in your GX and supply State of Charge (SoC) and other values to the inverter/charger.

## Documentation

* [Introduction](https://louisvdw.github.io/dbus-serialbattery/)
* [Features](https://louisvdw.github.io/dbus-serialbattery/general/features)
* [Supported BMS](https://louisvdw.github.io/dbus-serialbattery/general/supported-bms)
* [How to install, update, disable, enable and uninstall](https://louisvdw.github.io/dbus-serialbattery/general/install)
* [How to troubleshoot](https://louisvdw.github.io/dbus-serialbattery/troubleshoot/)
* [FAQ](https://louisvdw.github.io/dbus-serialbattery/faq/)

### Supporting this project
If you find this driver helpful please consider supporting this project. You can buy me a Ko-Fi or get in contact, if you would like to donate hardware for development.

### Support [Louisvdw](https://github.com/Louisvdw)
* Main developer
* Main developer until end of 2022
* Added most of the BMS drivers

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/Z8Z73LCW1) or using [Paypal.me](https://paypal.me/innernet)

### Support [mr-manuel](https://github.com/mr-manuel)
* Added a lot of features, optimizations and improvements with `v1.0.x`
* Assistance with the issues and discussions of forum
* Added a lot of documentation to the config file and notes that are displayed after installation for better understanding
* Introduced the new documentation page of the driver and reworked a great part of it for easier understanding

[<img src="https://github.md0.eu/uploads/donate-button.svg" height="38">](https://www.paypal.com/donate/?hosted_button_id=3NEVZBDM5KABW)

### Developer Remarks
To develop this project, install the requirements. This project makes use of velib_python which is pre-installed on
Venus-OS Devices under `/opt/victronenergy/dbus-systemcalc-py/ext/velib_python`. To use the python files locally,
`git clone` the [velib_python](https://github.com/victronenergy/velib_python) project to velib_python and add
velib_python to the `PYTHONPATH` environment variable.

Make sure the GitHub Actions run fine in your repository. In order to make the GitHub Actions run please select in your repository settings under `Actions` -> `General` -> `Actions permissions` the option `Allow all actions and reusable workflows`. Check also in your repository settings under `Actions` -> `General` -> `Workflow permissions` if `Read and write permissions` are selected. This will check your code for Flake8 and Black Lint errors. [Here](https://py-vscode.readthedocs.io/en/latest/files/linting.html) is a short instruction on how to set up Flake8 and Black Lint checks in VS Code. This will save you a lot of time.

See this checklist, if you want to [add a new BMS](https://louisvdw.github.io/dbus-serialbattery/general/supported-bms#add-by-opening-a-pull-request)

#### How it works
* Each supported BMS needs to implement the abstract base class `Battery` from `battery.py`.
* `dbus-serialbattery.py` tries to figure out the correct connected BMS by looping through all known implementations of
`Battery` and executing its `test_connection()`. If this returns true, `dbus-serialbattery.py` sticks with this battery
and then periodically executes `dbushelpert.publish_battery()`. `publish_battery()` executes `Battery.refresh_data()` which
updates the fields of Battery. It then publishes those fields to dbus using `dbushelper.publish_dbus()`
* The Victron Device will be "controlled" by the values published on `/Info/` - namely:
  * `/Info/MaxChargeCurrent `
  * `/Info/MaxDischargeCurrent`
  * `/Info/MaxChargeVoltage`
  * `/Info/BatteryLowVoltage`
  * `/Info/ChargeRequest` (not implemented in dbus-serialbattery)

For more details on the victron dbus interface see [the official victron dbus documentation](https://github.com/victronenergy/venus/wiki/dbus)

## Screenshots

### Venus OS

![VenusOS](docs/screenshots/venus-os_001.png)
![VenusOS](docs/screenshots/venus-os_002.png)
![VenusOS](docs/screenshots/venus-os_003.png)
![VenusOS](docs/screenshots/venus-os_004.png)
![VenusOS](docs/screenshots/venus-os_005.png)
![VenusOS](docs/screenshots/venus-os_006.png)
![VenusOS](docs/screenshots/venus-os_007.png)
![VenusOS](docs/screenshots/venus-os_008.png)
![VenusOS](docs/screenshots/venus-os_009.png)
![VenusOS](docs/screenshots/venus-os_010.png)
![VenusOS](docs/screenshots/venus-os_011.png)
![VenusOS](docs/screenshots/venus-os_012.png)
![VenusOS](docs/screenshots/venus-os_013.png)

### VRM Portal

![VenusOS](docs/screenshots/vrm-portal_001.png)
![VenusOS](docs/screenshots/vrm-portal_002.png)
![VenusOS](docs/screenshots/vrm-portal_003.png)
![VenusOS](docs/screenshots/vrm-portal_004.png)
![VenusOS](docs/screenshots/vrm-portal_005.png)
![VenusOS](docs/screenshots/vrm-portal_006.png)
![VenusOS](docs/screenshots/vrm-portal_007.png)
![VenusOS](docs/screenshots/vrm-portal_008.png)
![VenusOS](docs/screenshots/vrm-portal_009.png)
