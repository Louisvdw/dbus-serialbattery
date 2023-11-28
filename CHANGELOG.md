# Changelog

## Notes

* The Bluetooth and CAN connections are still not stable on some systems. If you want to have a stable connection use the serial connection.

## Breaking changes

* Driver version greater or equal to `v1.0.20231128beta`

  * The custom name is not saved to the config file anymore, but to the dbus service com.victronenergy.settings. You have to re-enter it once.

  * If you selected a specific device in `Settings -> System setup -> Battery monitor` and/or `Settings -> DVCC -> Controlling BMS` you have to reselect it.

* Driver version greater or equal to `v1.0.20230629beta` and smaller or equal to `v1.0.20230926beta`:

  With `v1.0.20230927beta` the following values changed names:
  * `BULK_CELL_VOLTAGE` -> `SOC_RESET_VOLTAGE`
  * `BULK_AFTER_DAYS` -> `SOC_RESET_AFTER_DAYS`

## v1.0.x

* Added: Bluetooth: Show signal strength of BMS in log by @mr-manuel
* Added: Configure logging level in `config.ini` by @mr-manuel
* Added: Create unique identifier, if not provided from BMS by @mr-manuel
* Added: Current average of the last 5 minutes by @mr-manuel
* Added: Daly BMS - Auto reset SoC when changing to float (can be turned off in the config file) by @transistorgit
* Added: Daly BMS connect via CAN (experimental, some limits apply) with https://github.com/Louisvdw/dbus-serialbattery/pull/169 by @SamuelBrucksch and @mr-manuel
* Added: Exclude a device from beeing used by the dbus-serialbattery driver by @mr-manuel
* Added: Implement callback function for update by @seidler2547
* Added: JKBMS BLE - Automatic SOC reset with https://github.com/Louisvdw/dbus-serialbattery/pull/736 by @ArendsM
* Added: JKBMS BLE - Show last five characters from the MAC address in the custom name (which is displayed in the device list) by @mr-manuel
* Added: JKBMS BMS connect via CAN (experimental, some limits apply) by @IrisCrimson and @mr-manuel
* Added: LLT/JBD BMS - Discharge / Charge Mosfet and disable / enable balancer switching over remote console/GUI with https://github.com/Louisvdw/dbus-serialbattery/pull/761 by @idstein
* Added: LLT/JBD BMS - Show balancer state in GUI under the IO page with https://github.com/Louisvdw/dbus-serialbattery/pull/763 by @idstein
* Added: Load to SOC reset voltage every x days to reset the SoC to 100% for some BMS by @mr-manuel
* Added: Save current charge state for driver restart or device reboot. Fixes https://github.com/Louisvdw/dbus-serialbattery/issues/840 by @mr-manuel
* Added: Save custom name and make it restart persistant by @mr-manuel
* Added: Temperature names to dbus and mqtt by @mr-manuel
* Added: The device instance does not change anymore when you plug the BMS into another USB port. Fixed https://github.com/Louisvdw/dbus-serialbattery/issues/718 by @mr-manuel
* Added: Use current average of the last 300 cycles for time to go and time to SoC calculation by @mr-manuel
* Added: Validate current, voltage, capacity and SoC for all BMS. This prevents that a device, which is no BMS, is detected as BMS. Fixes also https://github.com/Louisvdw/dbus-serialbattery/issues/479 by @mr-manuel
* Changed: `VOLTAGE_DROP` now behaves differently. Before it reduced the voltage for the check, now the voltage for the charger is increased in order to get the target voltage on the BMS by @mr-manuel
* Changed: Daly BMS - Fix readsentence by @transistorgit
* Changed: Daly BMS - Fixed https://github.com/Louisvdw/dbus-serialbattery/issues/837 by @mr-manuel
* Changed: Enable BMS that are disabled by default by specifying it in the config file. No more need to edit scripts by @mr-manuel
* Changed: Fixed Building wheel for dbus-fast won't finish on weak systems https://github.com/Louisvdw/dbus-serialbattery/issues/785 by @mr-manuel
* Changed: Fixed error in `reinstall-local.sh` script for Bluetooth installation by @mr-manuel
* Changed: Fixed meaningless Time to Go values by @transistorgit
* Changed: Fixed typo in `config.ini` sample by @hoschult
* Changed: For BMS_TYPE now multiple BMS can be specified by @mr-manuel
* Changed: Improved battery error handling on connection loss by @mr-manuel
* Changed: Improved battery voltage handling in linear absorption mode by @ogurevich
* Changed: Improved driver disable script by @md-manuel
* Changed: Improved driver reinstall when multiple Bluetooth BMS are enabled by @mr-manuel
* Changed: JKBMS - Driver do not start if manufacturer date in BMS is empty https://github.com/Louisvdw/dbus-serialbattery/issues/823 by @mr-manuel
* Changed: JKBMS_BLE BMS - Fixed MOSFET Temperature for HW 11 by @jensbehrens & @mr-manuel
* Changed: JKBMS_BLE BMS - Fixed recognition of newer models where no data is shown by @mr-manuel
* Changed: JKBMS_BLE BMS - Improved driver by @seidler2547 & @mr-manuel
* Changed: LLT/JBD BMS - Fix cycle capacity with https://github.com/Louisvdw/dbus-serialbattery/pull/762 by @idstein
* Changed: LLT/JBD BMS - Fixed https://github.com/Louisvdw/dbus-serialbattery/issues/730 by @mr-manuel
* Changed: LLT/JBD BMS - Fixed https://github.com/Louisvdw/dbus-serialbattery/issues/769 by @mr-manuel
* Changed: LLT/JBD BMS - Fixed https://github.com/Louisvdw/dbus-serialbattery/issues/778 with https://github.com/Louisvdw/dbus-serialbattery/pull/798 by @idstein
* Changed: LLT/JBD BMS - Improved error handling and automatical driver restart in case of error. Fixed https://github.com/Louisvdw/dbus-serialbattery/issues/777 by @mr-manuel
* Changed: LLT/JBD BMS - SOC different in Xiaoxiang app and dbus-serialbattery with https://github.com/Louisvdw/dbus-serialbattery/pull/760 by @idstein
* Changed: Make CCL and DCL limiting messages more clear by @mr-manuel
* Changed: Reduce the big inrush current if the CVL jumps from Bulk/Absorbtion to Float https://github.com/Louisvdw/dbus-serialbattery/issues/659 by @Rikkert-RS & @ogurevich
* Changed: Sinowealth BMS - Fix not loading https://github.com/Louisvdw/dbus-serialbattery/issues/702 by @mr-manuel
* Changed: Time-to-Go and Time-to-SoC use the current average of the last 5 minutes for calculation by @mr-manuel
* Changed: Time-to-SoC calculate only positive points by @mr-manuel
* Removed: Cronjob to restart Bluetooth service every 12 hours by @mr-manuel


## v1.0.20230531

### ATTENTION: Breaking changes! The config is now done in the `config.ini`. All values from the `utils.py` get lost. The changes in the `config.ini` will persists future updates.

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
* Changed: CVL calculation improvement. Removed cell voltage penalty. Replaced by automatic voltage calculation. Max voltage is kept until cells are balanced and reset when cells are inbalanced or SoC is below threshold by @mr-manuel
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
* Changed: Feedback from BMS driver to know, if BMS is found or not by @mr-manuel
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
* Changed: Renamed scripts for better reading #532 by @mr-manuel
* Changed: Reworked and optimized installation scripts by @mr-manuel
* Changed: Separate Time-To-Go and Time-To-SoC activation by @mr-manuel
* Changed: Serial-Starter file is now created from `reinstall-local.sh`. Fixes also https://github.com/Louisvdw/dbus-serialbattery/issues/520 by @mr-manuel
* Changed: Temperature alarm changed in order to not trigger all in the same condition for JKBMS by @mr-manuel
* Changed: Time-To-Soc repetition from cycles to seconds. Minimum value is every 5 seconds. This prevents CPU overload and ensures system stability. Renamed `TIME_TO_SOC_LOOP_CYCLES` to `TIME_TO_SOC_RECALCULATE_EVERY` by @mr-manuel
* Changed: Time-To-Soc string from `days, HR:MN:SC` to `<days>d <hours>h <minutes>m <seconds>s` (same as Time-To-Go) by @mr-manuel
* Changed: Uninstall also installed Bluetooth modules on uninstall by @mr-manuel
