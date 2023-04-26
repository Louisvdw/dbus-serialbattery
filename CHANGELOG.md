# Changelog

## v1.0.0

* Added: Balancing status for JKBMS
* Added: Balancing switch status for JKBMS
* Added: Balancing switch status to the GUI -> SerialBattery -> IO
* Added: Charge Mode display
* Added: Choose how battery temperature is assembled (mean temp 1 & 2, only temp 1 or only temp 2)
* Added: Create empty `config.ini` for easier user usage
* Added: Driver uninstall script
* Added: Fix for Venus OS >= v3.00~14 showing unused items https://github.com/Louisvdw/dbus-serialbattery/issues/469
* Added: HighInternalTemperature alarm (MOSFET) for JKBMS
* Added: Install needed components automatically after a Venus OS upgrade
* Added: Post install notes
* Added: Script to install directly from repository
* Added: Show charge mode (absorption, bulk, ...) in Parameters page
* Added: Show charge/discharge limitation reason
* Added: Show specific TimeToSoC points in GUI, if 0%, 10%, 20%, 80%, 90% and/or 100% are selected
* Added: Show TimeToGo in GUI only, if enabled
* Added: Temperature name for temperature sensor 1 & 2. This allows to see which sensor is low and high (e.g. battery and cable)
* Changed: `reinstalllocal.sh` to recreate `/data/conf/serial-starter.d` if deleted by `disabledriver.sh` --> to check if the file `conf/serial-starter.d` could now be removed from the repository
* Changed: Added QML to `restoregui.sh`
* Changed: Bash output
* Changed: Default config file
  * Added missing descriptions to make it much clearer to understand
  * Changed name from `default_config.ini` to `config.default.ini` https://github.com/Louisvdw/dbus-serialbattery/pull/412#issuecomment-1434287942
  * Changed TimeToSoc default value `TIME_TO_SOC_VALUE_TYPE` from `Both seconds and time string "<seconds> [<days>d <hours>h <minutes>m <seconds>s]"` to `1 Seconds`
  * Changed TimeToSoc description
  * Changed value positions, added groups and much clearer descriptions
* Changed: Fix for https://github.com/Louisvdw/dbus-serialbattery/issues/239
* Changed: Fix for https://github.com/Louisvdw/dbus-serialbattery/issues/311
* Changed: Fix for https://github.com/Louisvdw/dbus-serialbattery/issues/351
* Changed: Fix for https://github.com/Louisvdw/dbus-serialbattery/issues/421
* Changed: Fixed black lint errors
* Changed: Fixed cell balancing background for cells 17-24
* Changed: Fixed Time-To-Go is not working, if `TIME_TO_SOC_VALUE_TYPE` is set to other than `1` https://github.com/Louisvdw/dbus-serialbattery/pull/424#issuecomment-1440511018
* Changed: Logging to get relevant data
* Changed: Moved ble part to `installble.sh`
* Changed: Optimized installation scripts
* Changed: Serial-Starter file is now created from `reinstalllocal.sh`. Fixes also https://github.com/Louisvdw/dbus-serialbattery/issues/520
* Changed: Separate Time-To-Go and Time-To-SoC activation
* Changed: Temperature alarm changed in order to not trigger all in the same condition for JKBMS
* Changed: Time-To-Soc repetition from cycles to seconds. Minimum value is every 5 seconds. This prevents CPU overload and ensures system stability. Renamed `TIME_TO_SOC_LOOP_CYCLES` to `TIME_TO_SOC_RECALCULATE_EVERY`
* Changed: Time-To-Soc string from `days, HR:MN:SC` to `<days>d <hours>h <minutes>m <seconds>s` (same as Time-To-Go)
