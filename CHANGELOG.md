# Changelog

## v1.0.0

### ATTENTION: Breaking changes! The config is now done in the `config.ini`. All values from the `utils.py` gets lost. The changes in the `config.ini` will persists future updates.

* Added: `self.unique_identifier` to the battery class. Used to identify a BMS when multiple BMS are connected - planned for future use by @mr-manuel
* Added: Alert is triggered, when BMS communication is lost by @mr-manuel
* Added: Apply max voltage, if `CVCM_ENABLE` is `False`. Before float voltage was applied by @mr-manuel
* Added: Balancing status for JKBMS by @mr-manuel
* Added: Balancing switch status for JKBMS by @mr-manuel
* Added: Balancing switch status to the GUI -> SerialBattery -> IO by @mr-manuel
* Added: Block charge/discharge when BMS communication is lost. Can be enabled trough the config file by @mr-manuel
* Added: Charge Mode display by @mr-manuel
* Added: Check minimum required Venus OS version before installing by @mr-manuel
* Added: Choose how battery temperature is assembled (mean temp 1 & 2, only temp 1 or only temp 2) by @mr-manuel
* Added: Config file by @ppuetsch
* Added: Create empty `config.ini` for easier user usage by @mr-manuel
* Added: Cronjob to restart Bluetooth service every 12 hours by @mr-manuel
* Added: Daly BMS - Discharge / Charge Mosfet switching over remote console/GUI https://github.com/Louisvdw/dbus-serialbattery/issues/26 by @transistorgit
* Added: Daly BMS - Read capacity https://github.com/Louisvdw/dbus-serialbattery/pull/594 by @transistorgit
* Added: Daly BMS - Read production date and build unique identifier by @transistorgit
* Added: Daly BMS - Set SoC by @transistorgit
* Added: Daly BMS - Show "battery code" field that can be set in the Daly app by @transistorgit
* Added: Device name field (found in the GUI -> SerialBattery -> Device), that show a custom string that can be set in some BMS, if available by @mr-manuel
* Added: Driver uninstall script by @mr-manuel
* Added: Fix for Venus OS >= v3.00~14 showing unused items https://github.com/Louisvdw/dbus-serialbattery/issues/469 by @mr-manuel
* Added: HeltecSmartBMS driver by @ramack
* Added: HighInternalTemperature alarm (MOSFET) for JKBMS by @mr-manuel
* Added: HLPdata BMS driver by @ peterohman
* Added: Improved maintainability (flake8, black lint), introduced code checks and automate release build https://github.com/Louisvdw/dbus-serialbattery/pull/386 by @ppuetsch
* Added: Install needed Bluetooth components automatically after a Venus OS upgrade by @mr-manuel
* Added: JKBMS - MOS temperature https://github.com/Louisvdw/dbus-serialbattery/pull/440 by @baphomett
* Added: JKBMS - Uniqie identifier and show "User Private Data" field that can be set in the JKBMS App to identify the BMS in a multi battery environment by @mr-manuel
* Added: JKBMS BLE - Balancing switch status by @mr-manuel
* Added: JKBMS BLE - Capacity by @mr-manuel
* Added: JKBMS BLE - Cell imbalance alert by @mr-manuel
* Added: JKBMS BLE - Charging switch status by @mr-manuel
* Added: JKBMS BLE - Discharging switch status by @mr-manuel
* Added: JKBMS BLE - MOS temperature by @mr-manuel
* Added: JKBMS BLE - Show if balancing is active and which cells are balancing by @mr-manuel
* Added: JKBMS BLE - Show serial number and "User Private Data" field that can be set in the JKBMS App to identify the BMS in a multi battery environment by @mr-manuel
* Added: JKBMS BLE driver by @baranator
* Added: LLT/JBD BMS BLE driver by @idstein
* Added: Possibility to add `config.ini` to the root of a USB flash drive on install via the USB method by @mr-manuel
* Added: Possibility to configure a `VOLTAGE_DROP` voltage, if you are using a SmartShunt as battery monitor as there is a little voltage difference https://github.com/Louisvdw/dbus-serialbattery/discussions/632 by @mr-manuel
* Added: Post install notes by @mr-manuel
* Added: Read charge/discharge limits from JKBMS by @mr-manuel
* Added: Recalculation interval in linear mode for CVL, CCL and DCL by @mr-manuel
* Added: Rename TAR file after USB/SD card install to not overwrite the data on every reboot https://github.com/Louisvdw/dbus-serialbattery/issues/638 by @mr-manuel
* Added: Reset values to None, if battery goes offline (not reachable for 10s). Fixes https://github.com/Louisvdw/dbus-serialbattery/issues/193 https://github.com/Louisvdw/dbus-serialbattery/issues/64 by @transistorgit
* Added: Script to install directly from repository by @mr-manuel
* Added: Seplos BMS driver by @wollew
* Added: Serial number field (found in the GUI -> SerialBattery -> Device), that show the serial number or a unique identifier for the BMS, if available by @mr-manuel
* Added: Show charge mode (absorption, bulk, ...) in Parameters page by @mr-manuel
* Added: Show charge/discharge limitation reason by @mr-manuel
* Added: Show MOSFET temperature for JKBMS https://github.com/Louisvdw/dbus-serialbattery/pull/440 by @baphomett
* Added: Show serial number (used for unique identifier) and device name (custom BMS field) in the remote console/GUI to identify a BMS in a multi battery environment by @mr-manuel
* Added: Show specific TimeToSoC points in GUI, if 0%, 10%, 20%, 80%, 90% and/or 100% are selected by @mr-manuel
* Added: Show TimeToGo in GUI only, if enabled by @mr-manuel
* Added: Support for HLPdata BMS4S https://github.com/Louisvdw/dbus-serialbattery/pull/505 by @peterohman
* Added: Support for Seplos BMS https://github.com/Louisvdw/dbus-serialbattery/pull/530 by @wollew
* Added: Temperature 1-4 are now also available on the dbus and MQTT by @idstein
* Added: Temperature name for temperature sensor 1 & 2. This allows to see which sensor is low and high (e.g. battery and cable) by @mr-manuel
* Changed: `reinstall-local.sh` to recreate `/data/conf/serial-starter.d`, if deleted by `disable.sh` --> to check if the file `conf/serial-starter.d` could now be removed from the repository by @mr-manuel
* Changed: Added QML to `restore-gui.sh` by @mr-manuel
* Changed: Bash output by @mr-manuel
* Changed: Daly BMS - Fixed BMS alerts by @mr-manuel
* Changed: Daly BMS - Improved driver stability by @transistorgit & @mr-manuel
* Changed: Daly BMS - Reworked serial parser by @transistorgit
* Changed: Default config file by @ppuetsch
  * Added missing descriptions to make it much clearer to understand by @mr-manuel
  * Changed name from `default_config.ini` to `config.default.ini` https://github.com/Louisvdw/dbus-serialbattery/pull/412#issuecomment-1434287942 by @mr-manuel
  * Changed TimeToSoc default value `TIME_TO_SOC_VALUE_TYPE` from `Both seconds and time string "<seconds> [<days>d <hours>h <minutes>m <seconds>s]"` to `1 Seconds` by @mr-manuel
  * Changed TimeToSoc description by @mr-manuel
  * Changed value positions, added groups and much clearer descriptions by @mr-manuel
* Changed: Default FLOAT_CELL_VOLTAGE from 3.350 V to 3.375 V by @mr-manuel
* Changed: Default LINEAR_LIMITATION_ENABLE from False to True by @mr-manuel
* Changed: Disabled ANT BMS by default https://github.com/Louisvdw/dbus-serialbattery/issues/479 by @mr-manuel
* Changed: Driver can now also start without serial adapter attached for Bluetooth BMS by @seidler2547
* Changed: Fix for https://github.com/Louisvdw/dbus-serialbattery/issues/239 by @mr-manuel
* Changed: Fix for https://github.com/Louisvdw/dbus-serialbattery/issues/311 by @mr-manuel
* Changed: Fix for https://github.com/Louisvdw/dbus-serialbattery/issues/351 by @mr-manuel
* Changed: Fix for https://github.com/Louisvdw/dbus-serialbattery/issues/397 by @transistorgit
* Changed: Fix for https://github.com/Louisvdw/dbus-serialbattery/issues/421 by @mr-manuel
* Changed: Fix for https://github.com/Louisvdw/dbus-serialbattery/issues/450 by @mr-manuel
* Changed: Fix for https://github.com/Louisvdw/dbus-serialbattery/issues/648 by @mr-manuel
* Changed: Fixed black lint errors by @mr-manuel
* Changed: Fixed cell balancing background for cells 17-24 by @mr-manuel
* Changed: Fixed cell balancing display for JBD/LLT BMS https://github.com/Louisvdw/dbus-serialbattery/issues/359 by @mr-manuel
* Changed: Fixed Time-To-Go is not working, if `TIME_TO_SOC_VALUE_TYPE` is set to other than `1` https://github.com/Louisvdw/dbus-serialbattery/pull/424#issuecomment-1440511018 by @mr-manuel
* Changed: Improved install workflow via USB flash drive by @mr-manuel
* Changed: Improved JBD BMS soc calculation https://github.com/Louisvdw/dbus-serialbattery/pull/439 by @aaronreek
* Changed: Logging to get relevant data by @mr-manuel
* Changed: Many code improvements https://github.com/Louisvdw/dbus-serialbattery/pull/393 by @ppuetsch
* Changed: Moved Bluetooth part to `reinstall-local.sh` by @mr-manuel
* Changed: Moved BMS scripts to subfolder by @mr-manuel
* Changed: Removed all wildcard imports and fixed black lint errors by @mr-manuel
* Changed: CVL calculation improvement. Removed cell voltage penalty. Replaced by automatic voltage calculation. Max voltage is kept until cells are balanced and reset when cells are inbalanced or SoC is below threshold by @mr-manuel
* Changed: Renamed scripts for better reading #532 by @mr-manuel
* Changed: Reworked and optimized installation scripts by @mr-manuel
* Changed: Separate Time-To-Go and Time-To-SoC activation by @mr-manuel
* Changed: Serial-Starter file is now created from `reinstall-local.sh`. Fixes also https://github.com/Louisvdw/dbus-serialbattery/issues/520 by @mr-manuel
* Changed: Temperature alarm changed in order to not trigger all in the same condition for JKBMS by @mr-manuel
* Changed: Time-To-Soc repetition from cycles to seconds. Minimum value is every 5 seconds. This prevents CPU overload and ensures system stability. Renamed `TIME_TO_SOC_LOOP_CYCLES` to `TIME_TO_SOC_RECALCULATE_EVERY` by @mr-manuel
* Changed: Time-To-Soc string from `days, HR:MN:SC` to `<days>d <hours>h <minutes>m <seconds>s` (same as Time-To-Go) by @mr-manuel
* Changed: Uninstall also installed Bluetooth modules on uninstall by @mr-manuel
