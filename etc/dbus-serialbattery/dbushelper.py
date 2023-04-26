# -*- coding: utf-8 -*-
import sys
import os
import platform
import dbus
import traceback
from time import time

# Victron packages
sys.path.insert(
    1,
    os.path.join(
        os.path.dirname(__file__),
        "/opt/victronenergy/dbus-systemcalc-py/ext/velib_python",
    ),
)
from vedbus import VeDbusService
from settingsdevice import SettingsDevice
import battery
from utils import *


def get_bus():
    return (
        dbus.SessionBus()
        if "DBUS_SESSION_BUS_ADDRESS" in os.environ
        else dbus.SystemBus()
    )


class DbusHelper:
    def __init__(self, battery):
        self.battery = battery
        self.instance = 1
        self.settings = None
        self.error_count = 0
        self._dbusservice = VeDbusService(
            "com.victronenergy.battery."
            + self.battery.port[self.battery.port.rfind("/") + 1 :],
            get_bus(),
        )

    def setup_instance(self):
        # bms_id = self.battery.production if self.battery.production is not None else \
        #     self.battery.port[self.battery.port.rfind('/') + 1:]
        bms_id = self.battery.port[self.battery.port.rfind("/") + 1 :]
        path = "/Settings/Devices/serialbattery"
        default_instance = "battery:1"
        settings = {
            "instance": [
                path + "_" + str(bms_id).replace(" ", "_") + "/ClassAndVrmInstance",
                default_instance,
                0,
                0,
            ],
            # 'CellVoltageMin': [path + '/CellVoltageMin', 2.8, 0.0, 5.0],
            # 'CellVoltageMax': [path + '/CellVoltageMax', 3.45, 0.0, 5.0],
            # 'CellVoltageFloat': [path + '/CellVoltageFloat', 3.35, 0.0, 5.0],
            # 'VoltageMaxTime': [path + '/VoltageMaxTime', 900, 0, 0],
            # 'VoltageResetSocLimit': [path + '/VoltageResetSocLimit', 90, 0, 100],
            # 'MaxChargeCurrent': [path + '/MaxCurrentCharge', 5, 0.0, 500],
            # 'MaxDischargeCurrent': [path + '/MaxCurrentDischarge', 7, 0.0, 500],
            # 'AllowDynamicChargeCurrent': [path + '/AllowDynamicChargeCurrent', 1, 0, 1],
            # 'AllowDynamicDischargeCurrent': [path + '/AllowDynamicDischargeCurrent', 1, 0, 1],
            # 'AllowDynamicChargeVoltage': [path + '/AllowDynamicChargeVoltage', 0, 0, 1],
            # 'SocLowWarning': [path + '/SocLowWarning', 20, 0, 100],
            # 'SocLowAlarm': [path + '/SocLowAlarm', 10, 0, 100],
            # 'Capacity': [path + '/Capacity', '', 0, 500],
            # 'EnableInvertedCurrent': [path + '/EnableInvertedCurrent', 0, 0, 1],
            # 'CCMSocLimitCharge1': [path + '/CCMSocLimitCharge1', 98, 0, 100],
            # 'CCMSocLimitCharge2': [path + '/CCMSocLimitCharge2', 95, 0, 100],
            # 'CCMSocLimitCharge3': [path + '/CCMSocLimitCharge3', 91, 0, 100],
            # 'CCMSocLimitDischarge1': [path + '/CCMSocLimitDischarge1', 10, 0, 100],
            # 'CCMSocLimitDischarge2': [path + '/CCMSocLimitDischarge2', 20, 0, 100],
            # 'CCMSocLimitDischarge3': [path + '/CCMSocLimitDischarge3', 30, 0, 100],
            # 'CCMCurrentLimitCharge1': [path + '/CCMCurrentLimitCharge1', 5, 0, 100],
            # 'CCMCurrentLimitCharge2': [path + '/CCMCurrentLimitCharge2', '', 0, 100],
            # 'CCMCurrentLimitCharge3': [path + '/CCMCurrentLimitCharge3', '', 0, 100],
            # 'CCMCurrentLimitDischarge1': [path + '/CCMCurrentLimitDischarge1', 5, 0, 100],
            # 'CCMCurrentLimitDischarge2': [path + '/CCMCurrentLimitDischarge2', '', 0, 100],
            # 'CCMCurrentLimitDischarge3': [path + '/CCMCurrentLimitDischarge3', '', 0, 100],
        }

        self.settings = SettingsDevice(get_bus(), settings, self.handle_changed_setting)
        self.battery.role, self.instance = self.get_role_instance()

    def get_role_instance(self):
        val = self.settings["instance"].split(":")
        logger.info("DeviceInstance = %d", int(val[1]))
        return val[0], int(val[1])

    def handle_changed_setting(self, setting, oldvalue, newvalue):
        if setting == "instance":
            self.battery.role, self.instance = self.get_role_instance()
            logger.info("Changed DeviceInstance = %d", self.instance)
            return
        logger.info(
            "Changed DeviceInstance = %d", float(self.settings["CellVoltageMin"])
        )
        # self._dbusservice['/History/ChargeCycles']

    def setup_vedbus(self):
        # Set up dbus service and device instance
        # and notify of all the attributes we intend to update
        # This is only called once when a battery is initiated
        self.setup_instance()
        short_port = self.battery.port[self.battery.port.rfind("/") + 1 :]
        logger.info("%s" % ("com.victronenergy.battery." + short_port))

        # Get the settings for the battery
        if not self.battery.get_settings():
            return False

        # Create the management objects, as specified in the ccgx dbus-api document
        self._dbusservice.add_path("/Mgmt/ProcessName", __file__)
        self._dbusservice.add_path(
            "/Mgmt/ProcessVersion", "Python " + platform.python_version()
        )
        self._dbusservice.add_path("/Mgmt/Connection", "Serial " + self.battery.port)

        # Create the mandatory objects
        self._dbusservice.add_path("/DeviceInstance", self.instance)
        self._dbusservice.add_path("/ProductId", 0x0)
        self._dbusservice.add_path(
            "/ProductName", "SerialBattery(" + self.battery.type + ")"
        )
        self._dbusservice.add_path(
            "/FirmwareVersion", str(DRIVER_VERSION) + DRIVER_SUBVERSION
        )
        self._dbusservice.add_path("/HardwareVersion", self.battery.hardware_version)
        self._dbusservice.add_path("/Connected", 1)
        self._dbusservice.add_path(
            "/CustomName", "SerialBattery(" + self.battery.type + ")", writeable=True
        )

        # Create static battery info
        self._dbusservice.add_path(
            "/Info/BatteryLowVoltage", self.battery.min_battery_voltage, writeable=True
        )
        self._dbusservice.add_path(
            "/Info/MaxChargeVoltage",
            self.battery.max_battery_voltage,
            writeable=True,
            gettextcallback=lambda p, v: "{:0.2f}V".format(v),
        )
        self._dbusservice.add_path(
            "/Info/MaxChargeCurrent",
            self.battery.max_battery_charge_current,
            writeable=True,
            gettextcallback=lambda p, v: "{:0.2f}A".format(v),
        )
        self._dbusservice.add_path(
            "/Info/MaxDischargeCurrent",
            self.battery.max_battery_discharge_current,
            writeable=True,
            gettextcallback=lambda p, v: "{:0.2f}A".format(v),
        )
        self._dbusservice.add_path(
            "/System/NrOfCellsPerBattery", self.battery.cell_count, writeable=True
        )
        self._dbusservice.add_path("/System/NrOfModulesOnline", 1, writeable=True)
        self._dbusservice.add_path("/System/NrOfModulesOffline", 0, writeable=True)
        self._dbusservice.add_path(
            "/System/NrOfModulesBlockingCharge", None, writeable=True
        )
        self._dbusservice.add_path(
            "/System/NrOfModulesBlockingDischarge", None, writeable=True
        )
        self._dbusservice.add_path(
            "/Capacity",
            self.battery.get_capacity_remain(),
            writeable=True,
            gettextcallback=lambda p, v: "{:0.2f}Ah".format(v),
        )
        self._dbusservice.add_path(
            "/InstalledCapacity",
            self.battery.capacity,
            writeable=True,
            gettextcallback=lambda p, v: "{:0.0f}Ah".format(v),
        )
        self._dbusservice.add_path(
            "/ConsumedAmphours",
            None,
            writeable=True,
            gettextcallback=lambda p, v: "{:0.0f}Ah".format(v),
        )
        # Not used at this stage
        # self._dbusservice.add_path('/System/MinTemperatureCellId', None, writeable=True)
        # self._dbusservice.add_path('/System/MaxTemperatureCellId', None, writeable=True)

        # Create SOC, DC and System items
        self._dbusservice.add_path("/Soc", None, writeable=True)
        self._dbusservice.add_path(
            "/Dc/0/Voltage",
            None,
            writeable=True,
            gettextcallback=lambda p, v: "{:2.2f}V".format(v),
        )
        self._dbusservice.add_path(
            "/Dc/0/Current",
            None,
            writeable=True,
            gettextcallback=lambda p, v: "{:2.2f}A".format(v),
        )
        self._dbusservice.add_path(
            "/Dc/0/Power",
            None,
            writeable=True,
            gettextcallback=lambda p, v: "{:0.0f}W".format(v),
        )
        self._dbusservice.add_path("/Dc/0/Temperature", None, writeable=True)
        self._dbusservice.add_path(
            "/Dc/0/MidVoltage",
            None,
            writeable=True,
            gettextcallback=lambda p, v: "{:0.2f}V".format(v),
        )
        self._dbusservice.add_path(
            "/Dc/0/MidVoltageDeviation",
            None,
            writeable=True,
            gettextcallback=lambda p, v: "{:0.1f}%".format(v),
        )

        # Create battery extras
        self._dbusservice.add_path("/System/MinCellTemperature", None, writeable=True)
        self._dbusservice.add_path("/System/MaxCellTemperature", None, writeable=True)
        self._dbusservice.add_path("/System/MOSTemperature", None, writeable=True)
        self._dbusservice.add_path(
            "/System/MaxCellVoltage",
            None,
            writeable=True,
            gettextcallback=lambda p, v: "{:0.3f}V".format(v),
        )
        self._dbusservice.add_path("/System/MaxVoltageCellId", None, writeable=True)
        self._dbusservice.add_path(
            "/System/MinCellVoltage",
            None,
            writeable=True,
            gettextcallback=lambda p, v: "{:0.3f}V".format(v),
        )
        self._dbusservice.add_path("/System/MinVoltageCellId", None, writeable=True)
        self._dbusservice.add_path("/History/ChargeCycles", None, writeable=True)
        self._dbusservice.add_path("/History/TotalAhDrawn", None, writeable=True)
        self._dbusservice.add_path("/Balancing", None, writeable=True)
        self._dbusservice.add_path("/Io/AllowToCharge", 0, writeable=True)
        self._dbusservice.add_path("/Io/AllowToDischarge", 0, writeable=True)
        self._dbusservice.add_path("/Io/AllowToBalance", 0, writeable=True)
        self._dbusservice.add_path("/Io/ChargeMode", None, writeable=True)
        # self._dbusservice.add_path('/SystemSwitch', 1, writeable=True)

        # Create the alarms
        self._dbusservice.add_path("/Alarms/LowVoltage", None, writeable=True)
        self._dbusservice.add_path("/Alarms/HighVoltage", None, writeable=True)
        self._dbusservice.add_path("/Alarms/LowCellVoltage", None, writeable=True)
        self._dbusservice.add_path("/Alarms/HighCellVoltage", None, writeable=True)
        self._dbusservice.add_path("/Alarms/LowSoc", None, writeable=True)
        self._dbusservice.add_path("/Alarms/HighChargeCurrent", None, writeable=True)
        self._dbusservice.add_path("/Alarms/HighDischargeCurrent", None, writeable=True)
        self._dbusservice.add_path("/Alarms/CellImbalance", None, writeable=True)
        self._dbusservice.add_path("/Alarms/InternalFailure", None, writeable=True)
        self._dbusservice.add_path(
            "/Alarms/HighChargeTemperature", None, writeable=True
        )
        self._dbusservice.add_path("/Alarms/LowChargeTemperature", None, writeable=True)
        self._dbusservice.add_path("/Alarms/HighTemperature", None, writeable=True)
        self._dbusservice.add_path("/Alarms/LowTemperature", None, writeable=True)

        # cell voltages
        if BATTERY_CELL_DATA_FORMAT > 0:
            for i in range(1, self.battery.cell_count + 1):
                cellpath = (
                    "/Cell/%s/Volts"
                    if (BATTERY_CELL_DATA_FORMAT & 2)
                    else "/Voltages/Cell%s"
                )
                self._dbusservice.add_path(
                    cellpath % (str(i)),
                    None,
                    writeable=True,
                    gettextcallback=lambda p, v: "{:0.3f}V".format(v),
                )
                if BATTERY_CELL_DATA_FORMAT & 1:
                    self._dbusservice.add_path(
                        "/Balances/Cell%s" % (str(i)), None, writeable=True
                    )
            pathbase = "Cell" if (BATTERY_CELL_DATA_FORMAT & 2) else "Voltages"
            self._dbusservice.add_path(
                "/%s/Sum" % pathbase,
                None,
                writeable=True,
                gettextcallback=lambda p, v: "{:2.2f}V".format(v),
            )
            self._dbusservice.add_path(
                "/%s/Diff" % pathbase,
                None,
                writeable=True,
                gettextcallback=lambda p, v: "{:0.3f}V".format(v),
            )

        # Create TimeToSoC items only if enabled
        if self.battery.capacity is not None:
            # Create TimeToGo item
            if TIME_TO_GO_ENABLE:
                self._dbusservice.add_path("/TimeToGo", None, writeable=True)

            # Create TimeToSoc items
            if len(TIME_TO_SOC_POINTS) > 0:
                for num in TIME_TO_SOC_POINTS:
                    self._dbusservice.add_path(
                        "/TimeToSoC/" + str(num), None, writeable=True
                    )

        logger.info(f"publish config values = {PUBLISH_CONFIG_VALUES}")
        if PUBLISH_CONFIG_VALUES == 1:
            publish_config_variables(self._dbusservice)

        return True

    def publish_battery(self, loop):
        # This is called every battery.poll_interval milli second as set up per battery type to read and update the data
        try:
            # Call the battery's refresh_data function
            success = self.battery.refresh_data()
            if success:
                self.error_count = 0
                self.battery.online = True
            else:
                self.error_count += 1
                # If the battery is offline for more than 10 polls (polled every second for most batteries)
                if self.error_count >= 10:
                    self.battery.online = False
                # Has it completely failed
                if self.error_count >= 60:
                    loop.quit()

            # This is to mannage CCL\DCL
            self.battery.manage_charge_current()

            # This is to mannage CVCL
            self.battery.manage_charge_voltage()

            # publish all the data from the battery object to dbus
            self.publish_dbus()

        except:
            traceback.print_exc()
            loop.quit()

    def publish_dbus(self):
        # Update SOC, DC and System items
        self._dbusservice["/System/NrOfCellsPerBattery"] = self.battery.cell_count
        self._dbusservice["/Soc"] = round(self.battery.soc, 2)
        self._dbusservice["/Dc/0/Voltage"] = round(self.battery.voltage, 2)
        self._dbusservice["/Dc/0/Current"] = round(self.battery.current, 2)
        self._dbusservice["/Dc/0/Power"] = round(
            self.battery.voltage * self.battery.current, 2
        )
        self._dbusservice["/Dc/0/Temperature"] = self.battery.get_temp()
        self._dbusservice["/Capacity"] = self.battery.get_capacity_remain()
        self._dbusservice["/ConsumedAmphours"] = (
            None
            if self.battery.capacity is None
            or self.battery.get_capacity_remain() is None
            else self.battery.capacity - self.battery.get_capacity_remain()
        )

        midpoint, deviation = self.battery.get_midvoltage()
        if midpoint is not None:
            self._dbusservice["/Dc/0/MidVoltage"] = midpoint
            self._dbusservice["/Dc/0/MidVoltageDeviation"] = deviation

        # Update battery extras
        self._dbusservice["/History/ChargeCycles"] = self.battery.cycles
        self._dbusservice["/History/TotalAhDrawn"] = self.battery.total_ah_drawn
        self._dbusservice["/Io/AllowToCharge"] = (
            1 if self.battery.charge_fet and self.battery.control_allow_charge else 0
        )
        self._dbusservice["/Io/AllowToDischarge"] = (
            1
            if self.battery.discharge_fet and self.battery.control_allow_discharge
            else 0
        )
        self._dbusservice["/Io/AllowToBalance"] = 1 if self.battery.balance_fet else 0
        self._dbusservice["/Io/ChargeMode"] = self.battery.charge_mode
        self._dbusservice["/System/NrOfModulesBlockingCharge"] = (
            0
            if self.battery.charge_fet is None
            or (self.battery.charge_fet and self.battery.control_allow_charge)
            else 1
        )
        self._dbusservice["/System/NrOfModulesBlockingDischarge"] = (
            0 if self.battery.discharge_fet is None or self.battery.discharge_fet else 1
        )
        self._dbusservice["/System/NrOfModulesOnline"] = 1 if self.battery.online else 0
        self._dbusservice["/System/NrOfModulesOffline"] = (
            0 if self.battery.online else 1
        )
        self._dbusservice["/System/MinCellTemperature"] = self.battery.get_min_temp()
        self._dbusservice["/System/MaxCellTemperature"] = self.battery.get_max_temp()
        self._dbusservice["/System/MOSTemperature"] = self.battery.get_mos_temp()

        # Charge control
        self._dbusservice[
            "/Info/MaxChargeCurrent"
        ] = self.battery.control_charge_current
        self._dbusservice[
            "/Info/MaxDischargeCurrent"
        ] = self.battery.control_discharge_current

        # Voltage control
        self._dbusservice["/Info/MaxChargeVoltage"] = self.battery.control_voltage

        # Updates from cells
        self._dbusservice["/System/MinVoltageCellId"] = self.battery.get_min_cell_desc()
        self._dbusservice["/System/MaxVoltageCellId"] = self.battery.get_max_cell_desc()
        self._dbusservice[
            "/System/MinCellVoltage"
        ] = self.battery.get_min_cell_voltage()
        self._dbusservice[
            "/System/MaxCellVoltage"
        ] = self.battery.get_max_cell_voltage()
        self._dbusservice["/Balancing"] = self.battery.get_balancing()

        # Update the alarms
        self._dbusservice["/Alarms/LowVoltage"] = self.battery.protection.voltage_low
        self._dbusservice[
            "/Alarms/LowCellVoltage"
        ] = self.battery.protection.voltage_cell_low
        self._dbusservice["/Alarms/HighVoltage"] = self.battery.protection.voltage_high
        self._dbusservice["/Alarms/LowSoc"] = self.battery.protection.soc_low
        self._dbusservice[
            "/Alarms/HighChargeCurrent"
        ] = self.battery.protection.current_over
        self._dbusservice[
            "/Alarms/HighDischargeCurrent"
        ] = self.battery.protection.current_under
        self._dbusservice[
            "/Alarms/CellImbalance"
        ] = self.battery.protection.cell_imbalance
        self._dbusservice[
            "/Alarms/InternalFailure"
        ] = self.battery.protection.internal_failure
        self._dbusservice[
            "/Alarms/HighChargeTemperature"
        ] = self.battery.protection.temp_high_charge
        self._dbusservice[
            "/Alarms/LowChargeTemperature"
        ] = self.battery.protection.temp_low_charge
        self._dbusservice[
            "/Alarms/HighTemperature"
        ] = self.battery.protection.temp_high_discharge
        self._dbusservice[
            "/Alarms/LowTemperature"
        ] = self.battery.protection.temp_low_discharge

        # cell voltages
        if BATTERY_CELL_DATA_FORMAT > 0:
            try:
                voltageSum = 0
                for i in range(self.battery.cell_count):
                    voltage = self.battery.get_cell_voltage(i)
                    cellpath = (
                        "/Cell/%s/Volts"
                        if (BATTERY_CELL_DATA_FORMAT & 2)
                        else "/Voltages/Cell%s"
                    )
                    self._dbusservice[cellpath % (str(i + 1))] = voltage
                    if BATTERY_CELL_DATA_FORMAT & 1:
                        self._dbusservice[
                            "/Balances/Cell%s" % (str(i + 1))
                        ] = self.battery.get_cell_balancing(i)
                    if voltage:
                        voltageSum += voltage
                pathbase = "Cell" if (BATTERY_CELL_DATA_FORMAT & 2) else "Voltages"
                self._dbusservice["/%s/Sum" % pathbase] = voltageSum
                self._dbusservice["/%s/Diff" % pathbase] = (
                    self.battery.get_max_cell_voltage()
                    - self.battery.get_min_cell_voltage()
                )
            except:
                pass

        # Update TimeToSoC
        try:
            if (
                self.battery.capacity is not None
                and (TIME_TO_GO_ENABLE or len(TIME_TO_SOC_POINTS) > 0)
                and (
                    (
                        # update only once in same second
                        int(time()) != self.battery.time_to_soc_update
                        and
                        # update only every x seconds
                        int(time()) % TIME_TO_SOC_RECALCULATE_EVERY == 0
                    )
                    or
                    # update on first run
                    self.battery.time_to_soc_update == 0
                )
            ):
                self.battery.time_to_soc_update = int(time())
                crntPrctPerSec = (
                    abs(self.battery.current / (self.battery.capacity / 100)) / 3600
                )

                # Update TimeToGo item
                if TIME_TO_GO_ENABLE:
                    # Update TimeToGo item, has to be a positive int since it's used from dbus-systemcalc-py
                    self._dbusservice["/TimeToGo"] = (
                        abs(
                            int(
                                self.battery.get_timeToSoc(
                                    SOC_LOW_WARNING, crntPrctPerSec, True
                                )
                            )
                        )
                        if self.battery.current
                        else None
                    )

                # Update TimeToSoc items
                if len(TIME_TO_SOC_POINTS) > 0:
                    for num in TIME_TO_SOC_POINTS:
                        self._dbusservice["/TimeToSoC/" + str(num)] = (
                            self.battery.get_timeToSoc(num, crntPrctPerSec)
                            if self.battery.current
                            else None
                        )

        except:
            pass

        logger.debug("logged to dbus [%s]" % str(round(self.battery.soc, 2)))
        self.battery.log_cell_data()
