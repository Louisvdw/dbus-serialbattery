# Changelog

## v1.0.0

* Added: Balancing status for JKBMS by @mr-manuel
* Added: Balancing switch status for JKBMS by @mr-manuel
* Added: Balancing switch status to the GUI -> SerialBattery -> IO by @mr-manuel
* Added: `self.unique_identifier` to the battery class. Used to identify a BMS when multiple BMS are connected - planned for future use by @mr-manuel
* Added: Charge Mode display by @mr-manuel
* Added: Choose how battery temperature is assembled (mean temp 1 & 2, only temp 1 or only temp 2) by @mr-manuel
* Added: Config file by @ppuetsch
* Added: Create empty `config.ini` for easier user usage by @mr-manuel
* Added: Daly BMS read capacity https://github.com/Louisvdw/dbus-serialbattery/pull/594 by transistorgit
* Added: Driver uninstall script by @mr-manuel
* Added: Fix for Venus OS >= v3.00~14 showing unused items https://github.com/Louisvdw/dbus-serialbattery/issues/469 by @mr-manuel
* Added: HighInternalTemperature alarm (MOSFET) for JKBMS by @mr-manuel
* Added: Install needed components automatically after a Venus OS upgrade by @mr-manuel
* Added: Post install notes by @mr-manuel
* Added: Recalculation interval in linear mode for CVL, CCL and DCL by @mr-manuel
* Added: Script to install directly from repository by @mr-manuel
* Added: Show charge mode (absorption, bulk, ...) in Parameters page by @mr-manuel
* Added: Show charge/discharge limitation reason by @mr-manuel
* Added: Show MOSFET temperature for JKBMS https://github.com/Louisvdw/dbus-serialbattery/pull/440 by @baphomett
* Added: Show specific TimeToSoC points in GUI, if 0%, 10%, 20%, 80%, 90% and/or 100% are selected by @mr-manuel
* Added: Show TimeToGo in GUI only, if enabled by @mr-manuel
* Added: Support for HLPdata BMS4S https://github.com/Louisvdw/dbus-serialbattery/pull/505 by @peterohman
* Added: Support for Seplos BMS https://github.com/Louisvdw/dbus-serialbattery/pull/530 by @wollew
* Added: Temperature name for temperature sensor 1 & 2. This allows to see which sensor is low and high (e.g. battery and cable) by @mr-manuel
* Changed: `reinstalllocal.sh` to recreate `/data/conf/serial-starter.d` if deleted by `disabledriver.sh` --> to check if the file `conf/serial-starter.d` could now be removed from the repository by @mr-manuel
* Changed: Added QML to `restoregui.sh` by @mr-manuel
* Changed: Bash output by @mr-manuel
* Changed: Default config file by @mr-manuel
  * Added missing descriptions to make it much clearer to understand by @mr-manuel
  * Changed name from `default_config.ini` to `config.default.ini` https://github.com/Louisvdw/dbus-serialbattery/pull/412#issuecomment-1434287942 by @mr-manuel
  * Changed TimeToSoc default value `TIME_TO_SOC_VALUE_TYPE` from `Both seconds and time string "<seconds> [<days>d <hours>h <minutes>m <seconds>s]"` to `1 Seconds` by @mr-manuel
  * Changed TimeToSoc description by @mr-manuel
  * Changed value positions, added groups and much clearer descriptions by @mr-manuel
* Changed: Disabled ANT BMS by default https://github.com/Louisvdw/dbus-serialbattery/issues/479 by @mr-manuel
* Changed: Fix for https://github.com/Louisvdw/dbus-serialbattery/issues/239 by @mr-manuel
* Changed: Fix for https://github.com/Louisvdw/dbus-serialbattery/issues/311 by @mr-manuel
* Changed: Fix for https://github.com/Louisvdw/dbus-serialbattery/issues/351 by @mr-manuel
* Changed: Fix for https://github.com/Louisvdw/dbus-serialbattery/issues/397 by @transistorgit
* Changed: Fix for https://github.com/Louisvdw/dbus-serialbattery/issues/421 by @mr-manuel
* Changed: Fixed black lint errors by @mr-manuel
* Changed: Fixed cell balancing background for cells 17-24 by @mr-manuel
* Changed: Fixed Time-To-Go is not working, if `TIME_TO_SOC_VALUE_TYPE` is set to other than `1` https://github.com/Louisvdw/dbus-serialbattery/pull/424#issuecomment-1440511018 by @mr-manuel
* Changed: Improved JBD BMS soc calculation https://github.com/Louisvdw/dbus-serialbattery/pull/439 by @aaronreek
* Changed: Logging to get relevant data by @mr-manuel
* Changed: Moved BMS scripts to subfolder by @mr-manuel
* Changed: Optimized installation scripts by @mr-manuel* Changed: Removed cell voltage penalty. Replaced by automatic voltage calculation. Max voltage is kept until cells are balanced and reset when cells are inbalanced by @mr-manuel
* Changed: Removed cell voltage penalty. Replaced by automatic voltage calculation. Max voltage is kept until cells are balanced and reset when cells are inbalanced by @mr-manuel
* Changed: Removed wildcard imports from several BMS drivers and fixed black lint errors by @mr-manuel
* Changed: Serial-Starter file is now created from `reinstalllocal.sh`. Fixes also https://github.com/Louisvdw/dbus-serialbattery/issues/520 by @mr-manuel
* Changed: Separate Time-To-Go and Time-To-SoC activation by @mr-manuel
* Changed: Temperature alarm changed in order to not trigger all in the same condition for JKBMS by @mr-manuel
* Changed: Time-To-Soc repetition from cycles to seconds. Minimum value is every 5 seconds. This prevents CPU overload and ensures system stability. Renamed `TIME_TO_SOC_LOOP_CYCLES` to `TIME_TO_SOC_RECALCULATE_EVERY` by @mr-manuel
* Changed: Time-To-Soc string from `days, HR:MN:SC` to `<days>d <hours>h <minutes>m <seconds>s` (same as Time-To-Go) by @mr-manuel
