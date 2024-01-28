# -*- coding: utf-8 -*-
import sys
import os
import platform
import dbus  # pyright: ignore[reportMissingImports]
import traceback
from time import time
from utils import logger, publish_config_variables
import utils
from xml.etree import ElementTree

# Victron packages
sys.path.insert(
    1,
    os.path.join(
        os.path.dirname(__file__),
        "/opt/victronenergy/dbus-systemcalc-py/ext/velib_python",
    ),
)
from vedbus import VeDbusService  # noqa: E402
from settingsdevice import (  # noqa: E402
    SettingsDevice,
)


def get_bus() -> dbus.bus.BusConnection:
    return (
        dbus.SessionBus()
        if "DBUS_SESSION_BUS_ADDRESS" in os.environ
        else dbus.SystemBus()
    )


class DbusHelper:
    EMPTY_DICT = {}

    def __init__(self, battery):
        self.battery = battery
        self.instance = 1
        self.settings = None
        self.error = {"count": 0, "timestamp_first": None, "timestamp_last": None}
        self.block_because_disconnect = False
        self.cell_voltages_good = False
        self._dbusservice = VeDbusService(
            "com.victronenergy.battery."
            + self.battery.port[self.battery.port.rfind("/") + 1 :],
            get_bus(),
        )
        self.bms_id = "".join(
            # remove all non alphanumeric characters from the identifier
            c if c.isalnum() else "_"
            for c in self.battery.unique_identifier()
        )
        self.path_battery = None
        self.save_charge_details_last = {
            "allow_max_voltage": self.battery.allow_max_voltage,
            "max_voltage_start_time": self.battery.max_voltage_start_time,
            "soc_reset_last_reached": self.battery.soc_reset_last_reached,
            "soc_calc": self.battery.soc_calc
            if self.battery.soc_calc is not None
            else "",
        }

    def setup_instance(self):
        # checks if the battery was already connected once
        # if so, get the instance from the dbus settings and update last seen with current time
        # if not, create the settings and set the instance to the next available one

        # bms_id = self.battery.production if self.battery.production is not None else \
        #     self.battery.port[self.battery.port.rfind('/') + 1:]
        # bms_id = self.battery.port[self.battery.port.rfind("/") + 1 :]
        logger.debug("setup_instance(): start")

        custom_name = self.battery.custom_name()
        device_instance = "1"
        device_instances_used = []
        found_bms = False
        self.path_battery = "/Settings/Devices/serialbattery" + "_" + str(self.bms_id)

        # prepare settings class
        self.settings = SettingsDevice(
            get_bus(), self.EMPTY_DICT, self.handle_changed_setting
        )
        logger.debug("setup_instance(): SettingsDevice")

        # get all the settings from the dbus
        settings_from_dbus = self.getSettingsWithValues(
            get_bus(),
            "com.victronenergy.settings",
            "/Settings/Devices",
        )
        logger.debug("setup_instance(): getSettingsWithValues")
        # output:
        # {
        #     "Settings": {
        #         "Devices": {
        #             "serialbattery_JK_B2A20S20P": {
        #                 "AllowMaxVoltage",
        #                 "ClassAndVrmInstance": "battery:3",
        #                 "CustomName": "My Battery 1",
        #                 "LastSeen": "1700926114",
        #                 "MaxVoltageStartTime": "",
        #                 "SocResetLastReached": 0,
        #                 "UniqueIdentifier": "JK_B2A20S20P",
        #             },
        #             "serialbattery_JK_B2A20S25P": {
        #                 "AllowMaxVoltage",
        #                 "ClassAndVrmInstance": "battery:4",
        #                 "CustomName": "My Battery 2",
        #                 "LastSeen": "1700926114",
        #                 "MaxVoltageStartTime": "",
        #                 "SocResetLastReached": 0,
        #                 "UniqueIdentifier": "JK_B2A20S25P",
        #             },
        #             "serialbattery_ttyUSB0": {
        #                 "ClassAndVrmInstance": "battery:1",
        #             },
        #             "serialbattery_ttyUSB1": {
        #                 "ClassAndVrmInstance": "battery:2",
        #             },
        #             "vegps_ttyUSB0": {
        #                 "ClassAndVrmInstance": "gps:0"
        #             },
        #         }
        #     }
        # }

        # loop through devices in dbus settings
        if (
            "Settings" in settings_from_dbus
            and "Devices" in settings_from_dbus["Settings"]
        ):
            for key, value in settings_from_dbus["Settings"]["Devices"].items():
                # check if it's a serialbattery
                if "serialbattery" in key:
                    # check used device instances
                    if "ClassAndVrmInstance" in value:
                        device_instances_used.append(
                            value["ClassAndVrmInstance"][
                                value["ClassAndVrmInstance"].rfind(":") + 1 :
                            ]
                        )

                    # check the unique identifier, if the battery was already connected once
                    # if so, get the last saved data
                    if (
                        "UniqueIdentifier" in value
                        and value["UniqueIdentifier"] == self.bms_id
                    ):
                        # set found_bms to true
                        found_bms = True

                        # get the instance from the object name
                        device_instance = int(
                            value["ClassAndVrmInstance"][
                                value["ClassAndVrmInstance"].rfind(":") + 1 :
                            ]
                        )
                        logger.info(
                            f"Found existing battery with DeviceInstance = {device_instance}"
                        )

                        if "AllowMaxVoltage" in value and isinstance(
                            value["AllowMaxVoltage"], int
                        ):
                            self.battery.allow_max_voltage = (
                                True if value["AllowMaxVoltage"] == 1 else False
                            )
                            self.battery.max_voltage_start_time = None

                        # check if the battery has a custom name
                        if "CustomName" in value and value["CustomName"] != "":
                            custom_name = value["CustomName"]

                        if "MaxVoltageStartTime" in value and isinstance(
                            value["MaxVoltageStartTime"], int
                        ):
                            self.battery.max_voltage_start_time = int(
                                value["MaxVoltageStartTime"]
                            )

                        # load SOC from dbus only if SOC_CALCULATION is enabled
                        if utils.SOC_CALCULATION:
                            if "SocCalc" in value:
                                self.battery.soc_calc = float(value["SocCalc"])
                                logger.info(
                                    f"Soc_calc read from dbus: {self.battery.soc_calc}"
                                )
                            else:
                                logger.info("Soc_calc not found in dbus")

                        if "SocResetLastReached" in value and isinstance(
                            value["SocResetLastReached"], int
                        ):
                            self.battery.soc_reset_last_reached = int(
                                value["SocResetLastReached"]
                            )

                    # check the last seen time and remove the battery it it was not seen for 30 days
                    elif "LastSeen" in value and int(value["LastSeen"]) < int(
                        time()
                    ) - (60 * 60 * 24 * 30):
                        # remove entry
                        del_return = self.removeSetting(
                            get_bus(),
                            "com.victronenergy.settings",
                            "/Settings/Devices/" + key,
                            [
                                "AllowMaxVoltage",
                                "ClassAndVrmInstance",
                                "CustomName",
                                "LastSeen",
                                "MaxVoltageStartTime",
                                "SocCalc",
                                "SocResetLastReached",
                                "UniqueIdentifier",
                            ],
                        )
                        logger.info(
                            f"Remove /Settings/Devices/{key} from dbus. Delete result: {del_return}"
                        )

                    # check if the battery has a last seen time, if not then it's an old entry and can be removed
                    elif "LastSeen" not in value:
                        del_return = self.removeSetting(
                            get_bus(),
                            "com.victronenergy.settings",
                            "/Settings/Devices/" + key,
                            ["ClassAndVrmInstance"],
                        )
                        logger.info(
                            f"Remove /Settings/Devices/{key} from dbus. "
                            + f"Old entry. Delete result: {del_return}"
                        )

                if "ruuvi" in key:
                    # check if Ruuvi tag is enabled, if not remove entry.
                    if (
                        "Enabled" in value
                        and value["Enabled"] == "0"
                        and "ClassAndVrmInstance" not in value
                    ):
                        del_return = self.removeSetting(
                            get_bus(),
                            "com.victronenergy.settings",
                            "/Settings/Devices/" + key,
                            ["CustomName", "Enabled", "TemperatureType"],
                        )
                        logger.info(
                            f"Remove /Settings/Devices/{key} from dbus. "
                            + f"Ruuvi tag was disabled and had no ClassAndVrmInstance. Delete result: {del_return}"
                        )

        logger.debug("setup_instance(): for loop ended")

        # create class and crm instance
        class_and_vrm_instance = "battery:" + str(device_instance)

        # preare settings and write them to com.victronenergy.settings
        settings = {
            "AllowMaxVoltage": [
                self.path_battery + "/AllowMaxVoltage",
                1 if self.battery.allow_max_voltage else 0,
                0,
                0,
            ],
            "ClassAndVrmInstance": [
                self.path_battery + "/ClassAndVrmInstance",
                class_and_vrm_instance,
                0,
                0,
            ],
            "CustomName": [
                self.path_battery + "/CustomName",
                custom_name,
                0,
                0,
            ],
            "LastSeen": [
                self.path_battery + "/LastSeen",
                int(time()),
                0,
                0,
            ],
            "MaxVoltageStartTime": [
                self.path_battery + "/MaxVoltageStartTime",
                self.battery.max_voltage_start_time
                if self.battery.max_voltage_start_time is not None
                else "",
                0,
                0,
            ],
            "SocCalc": [
                self.path_battery + "/SocCalc",
                self.battery.soc_calc if self.battery.soc_calc is not None else "",
                0,
                0,
            ],
            "SocResetLastReached": [
                self.path_battery + "/SocResetLastReached",
                self.battery.soc_reset_last_reached,
                0,
                0,
            ],
            "UniqueIdentifier": [
                self.path_battery + "/UniqueIdentifier",
                self.bms_id,
                0,
                0,
            ],
        }

        # update last seen
        if found_bms:
            self.setSetting(
                get_bus(),
                "com.victronenergy.settings",
                self.path_battery,
                "LastSeen",
                int(time()),
            )

        self.settings.addSettings(settings)
        self.battery.role, self.instance = self.get_role_instance()

        logger.info(f"Used device instances: {device_instances_used}")

    def update_last_seen(self):
        # update the last seen time
        self.settings.addSetting(
            "/Settings/Devices/serialbattery" + "_" + str(self.bms_id) + "/LastSeen",
            int(time()),
            0,
            0,
        )

    def get_role_instance(self):
        val = self.settings["ClassAndVrmInstance"].split(":")
        logger.info("DeviceInstance = %d", int(val[1]))
        return val[0], int(val[1])

    def handle_changed_setting(self, setting, oldvalue, newvalue):
        if setting == "ClassAndVrmInstance":
            self.battery.role, self.instance = self.get_role_instance()
            logger.info(f"Changed DeviceInstance = {self.instance}")
            return
        if setting == "CustomName":
            logger.info(f"Changed CustomName = {newvalue}")
            return

    # this function is called when the battery is initiated
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
        self._dbusservice.add_path("/Mgmt/Connection", self.battery.connection_name())

        # Create the mandatory objects
        self._dbusservice.add_path("/DeviceInstance", self.instance)
        self._dbusservice.add_path("/ProductId", 0x0)
        self._dbusservice.add_path("/ProductName", self.battery.product_name())
        self._dbusservice.add_path("/FirmwareVersion", str(utils.DRIVER_VERSION))
        self._dbusservice.add_path("/HardwareVersion", self.battery.hardware_version)
        self._dbusservice.add_path("/Connected", 1)
        self._dbusservice.add_path(
            "/CustomName",
            self.settings["CustomName"],
            writeable=True,
            onchangecallback=self.custom_name_callback,
        )
        self._dbusservice.add_path("/Serial", self.bms_id, writeable=True)
        self._dbusservice.add_path(
            "/DeviceName", self.battery.custom_field, writeable=True
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

        self._dbusservice.add_path("/Info/ChargeMode", None, writeable=True)
        self._dbusservice.add_path("/Info/ChargeModeDebug", None, writeable=True)
        self._dbusservice.add_path("/Info/ChargeLimitation", None, writeable=True)
        self._dbusservice.add_path("/Info/DischargeLimitation", None, writeable=True)

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

        # Create SOC, DC and System items
        self._dbusservice.add_path("/Soc", None, writeable=True)
        # add original SOC for comparing
        if utils.SOC_CALCULATION:
            self._dbusservice.add_path("/SocBms", None, writeable=True)

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
        self._dbusservice.add_path("/System/MinTemperatureCellId", None, writeable=True)
        self._dbusservice.add_path("/System/MaxCellTemperature", None, writeable=True)
        self._dbusservice.add_path("/System/MaxTemperatureCellId", None, writeable=True)
        self._dbusservice.add_path("/System/MOSTemperature", None, writeable=True)
        self._dbusservice.add_path("/System/Temperature1", None, writeable=True)
        self._dbusservice.add_path("/System/Temperature1Name", None, writeable=True)
        self._dbusservice.add_path("/System/Temperature2", None, writeable=True)
        self._dbusservice.add_path("/System/Temperature2Name", None, writeable=True)
        self._dbusservice.add_path("/System/Temperature3", None, writeable=True)
        self._dbusservice.add_path("/System/Temperature3Name", None, writeable=True)
        self._dbusservice.add_path("/System/Temperature4", None, writeable=True)
        self._dbusservice.add_path("/System/Temperature4Name", None, writeable=True)
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
        self._dbusservice.add_path(
            "/Io/ForceChargingOff",
            0,
            writeable=True,
            onchangecallback=self.battery.force_charging_off_callback,
        )
        self._dbusservice.add_path(
            "/Io/ForceDischargingOff",
            0,
            writeable=True,
            onchangecallback=self.battery.force_discharging_off_callback,
        )
        self._dbusservice.add_path(
            "/Io/TurnBalancingOff",
            0,
            writeable=True,
            onchangecallback=self.battery.turn_balancing_off_callback,
        )
        # self._dbusservice.add_path('/SystemSwitch', 1, writeable=True)

        # Create the alarms
        self._dbusservice.add_path("/Alarms/LowVoltage", None, writeable=True)
        self._dbusservice.add_path("/Alarms/HighVoltage", None, writeable=True)
        self._dbusservice.add_path("/Alarms/LowCellVoltage", None, writeable=True)
        # self._dbusservice.add_path("/Alarms/HighCellVoltage", None, writeable=True)  ## does not exist on the dbus
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
        self._dbusservice.add_path("/Alarms/BmsCable", None, writeable=True)
        self._dbusservice.add_path(
            "/Alarms/HighInternalTemperature", None, writeable=True
        )

        # cell voltages
        if utils.BATTERY_CELL_DATA_FORMAT > 0:
            for i in range(1, self.battery.cell_count + 1):
                cellpath = (
                    "/Cell/%s/Volts"
                    if (utils.BATTERY_CELL_DATA_FORMAT & 2)
                    else "/Voltages/Cell%s"
                )
                self._dbusservice.add_path(
                    cellpath % (str(i)),
                    None,
                    writeable=True,
                    gettextcallback=lambda p, v: "{:0.3f}V".format(v),
                )
                if utils.BATTERY_CELL_DATA_FORMAT & 1:
                    self._dbusservice.add_path(
                        "/Balances/Cell%s" % (str(i)), None, writeable=True
                    )
            pathbase = "Cell" if (utils.BATTERY_CELL_DATA_FORMAT & 2) else "Voltages"
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
            if utils.TIME_TO_GO_ENABLE:
                self._dbusservice.add_path("/TimeToGo", None, writeable=True)
                self._dbusservice.add_path(
                    "/CurrentAvg",
                    None,
                    writeable=True,
                    gettextcallback=lambda p, v: "{:0.2f}A".format(v),
                )

            # Create TimeToSoc items
            if len(utils.TIME_TO_SOC_POINTS) > 0:
                for num in utils.TIME_TO_SOC_POINTS:
                    self._dbusservice.add_path(
                        "/TimeToSoC/" + str(num), None, writeable=True
                    )

        logger.info(f"publish config values = {utils.PUBLISH_CONFIG_VALUES}")
        if utils.PUBLISH_CONFIG_VALUES:
            publish_config_variables(self._dbusservice)

        if self.battery.has_settings:
            self._dbusservice.add_path("/Settings/HasSettings", 1, writeable=False)
            self._dbusservice.add_path(
                "/Settings/ResetSoc",
                0,
                writeable=True,
                onchangecallback=self.battery.reset_soc_callback,
            )

        return True

    def publish_battery(self, loop):
        # This is called every battery.poll_interval milli second as set up per battery type to read and update the data
        try:
            # Call the battery's refresh_data function
            result = self.battery.refresh_data()
            if result:
                # reset error variables
                self.error["count"] = 0
                self.battery.online = True

                # unblock charge/discharge, if it was blocked when battery went offline
                if utils.BLOCK_ON_DISCONNECT:
                    self.block_because_disconnect = False

            else:
                # update error variables
                if self.error["count"] == 0:
                    self.error["timestamp_first"] = int(time())
                self.error["timestamp_last"] = int(time())
                self.error["count"] += 1

                time_since_first_error = (
                    self.error["timestamp_last"] - self.error["timestamp_first"]
                )

                # if the battery did not update in 10 second, it's assumed to be offline
                if time_since_first_error >= 10 and self.battery.online:
                    self.battery.online = False

                    # check if the cell voltages are good to go for some minutes
                    self.cell_voltages_good = (
                        True
                        if self.battery.get_min_cell_voltage() > 3.25
                        and self.battery.get_max_cell_voltage() < 3.35
                        else False
                    )

                    # reset the battery values
                    self.battery.init_values()

                    # block charge/discharge
                    if utils.BLOCK_ON_DISCONNECT:
                        self.block_because_disconnect = True

                # if the battery did not update in 60 second, it's assumed to be completely failed
                if time_since_first_error >= 60 and (
                    utils.BLOCK_ON_DISCONNECT or not self.cell_voltages_good
                ):
                    loop.quit()

                # if the cells are between 3.2 and 3.3 volt we can continue for some time
                if time_since_first_error >= 60 * 20 and not utils.BLOCK_ON_DISCONNECT:
                    loop.quit()

            # This is to mannage CVCL
            self.battery.manage_charge_voltage()

            # This is to mannage CCL\DCL
            self.battery.manage_charge_current()

            # publish all the data from the battery object to dbus
            self.publish_dbus()

        except Exception:
            traceback.print_exc()
            loop.quit()

    def publish_dbus(self):
        # Update SOC, DC and System items
        self._dbusservice["/System/NrOfCellsPerBattery"] = self.battery.cell_count
        if utils.SOC_CALCULATION:
            self._dbusservice["/Soc"] = (
                round(self.battery.soc_calc, 2)
                if self.battery.soc_calc is not None
                else None
            )
            # add original SOC for comparing
            self._dbusservice["/SocBms"] = (
                round(self.battery.soc, 2) if self.battery.soc is not None else None
            )
        else:
            self._dbusservice["/Soc"] = (
                round(self.battery.soc, 2) if self.battery.soc is not None else None
            )
        self._dbusservice["/Dc/0/Voltage"] = (
            round(self.battery.voltage, 2) if self.battery.voltage is not None else None
        )
        self._dbusservice["/Dc/0/Current"] = (
            round(self.battery.current, 2) if self.battery.current is not None else None
        )
        self._dbusservice["/Dc/0/Power"] = (
            round(self.battery.voltage * self.battery.current, 2)
            if self.battery.current is not None and self.battery.current is not None
            else None
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
            1
            if self.battery.charge_fet
            and self.battery.control_allow_charge
            and self.block_because_disconnect is False
            else 0
        )
        self._dbusservice["/Io/AllowToDischarge"] = (
            1
            if self.battery.discharge_fet
            and self.battery.control_allow_discharge
            and self.block_because_disconnect is False
            else 0
        )
        self._dbusservice["/Io/AllowToBalance"] = 1 if self.battery.balance_fet else 0
        self._dbusservice["/System/NrOfModulesBlockingCharge"] = (
            0
            if (
                self.battery.charge_fet is None
                or (self.battery.charge_fet and self.battery.control_allow_charge)
            )
            and self.block_because_disconnect is False
            else 1
        )
        self._dbusservice["/System/NrOfModulesBlockingDischarge"] = (
            0
            if (self.battery.discharge_fet is None or self.battery.discharge_fet)
            and self.block_because_disconnect is False
            else 1
        )
        self._dbusservice["/System/NrOfModulesOnline"] = 1 if self.battery.online else 0
        self._dbusservice["/System/NrOfModulesOffline"] = (
            0 if self.battery.online else 1
        )
        self._dbusservice["/System/MinCellTemperature"] = self.battery.get_min_temp()
        self._dbusservice[
            "/System/MinTemperatureCellId"
        ] = self.battery.get_min_temp_id()
        self._dbusservice["/System/MaxCellTemperature"] = self.battery.get_max_temp()
        self._dbusservice[
            "/System/MaxTemperatureCellId"
        ] = self.battery.get_max_temp_id()
        self._dbusservice["/System/MOSTemperature"] = self.battery.get_mos_temp()
        self._dbusservice["/System/Temperature1"] = self.battery.temp1
        self._dbusservice["/System/Temperature1Name"] = utils.TEMP_1_NAME
        self._dbusservice["/System/Temperature2"] = self.battery.temp2
        self._dbusservice["/System/Temperature2Name"] = utils.TEMP_2_NAME
        self._dbusservice["/System/Temperature3"] = self.battery.temp3
        self._dbusservice["/System/Temperature3Name"] = utils.TEMP_3_NAME
        self._dbusservice["/System/Temperature4"] = self.battery.temp4
        self._dbusservice["/System/Temperature4Name"] = utils.TEMP_4_NAME

        # Voltage control
        self._dbusservice["/Info/MaxChargeVoltage"] = (
            round(self.battery.control_voltage + utils.VOLTAGE_DROP, 2)
            if self.battery.control_voltage is not None
            else None
        )

        # Charge control
        self._dbusservice[
            "/Info/MaxChargeCurrent"
        ] = self.battery.control_charge_current
        self._dbusservice[
            "/Info/MaxDischargeCurrent"
        ] = self.battery.control_discharge_current

        # Voltage and charge control info
        self._dbusservice["/Info/ChargeMode"] = self.battery.charge_mode
        self._dbusservice["/Info/ChargeModeDebug"] = self.battery.charge_mode_debug
        self._dbusservice["/Info/ChargeLimitation"] = self.battery.charge_limitation
        self._dbusservice[
            "/Info/DischargeLimitation"
        ] = self.battery.discharge_limitation

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
        # disable high voltage warning temporarly, if loading to bulk voltage and bulk voltage reached is 30 minutes ago
        self._dbusservice["/Alarms/HighVoltage"] = (
            self.battery.protection.voltage_high
            if (
                self.battery.soc_reset_requested is False
                and self.battery.soc_reset_last_reached < int(time()) - (60 * 30)
            )
            else 0
        )
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
        self._dbusservice["/Alarms/BmsCable"] = (
            2 if self.block_because_disconnect else 0
        )
        self._dbusservice[
            "/Alarms/HighInternalTemperature"
        ] = self.battery.protection.temp_high_internal

        # cell voltages
        if utils.BATTERY_CELL_DATA_FORMAT > 0:
            try:
                voltage_sum = 0
                for i in range(self.battery.cell_count):
                    voltage = self.battery.get_cell_voltage(i)
                    cellpath = (
                        "/Cell/%s/Volts"
                        if (utils.BATTERY_CELL_DATA_FORMAT & 2)
                        else "/Voltages/Cell%s"
                    )
                    self._dbusservice[cellpath % (str(i + 1))] = voltage
                    if utils.BATTERY_CELL_DATA_FORMAT & 1:
                        self._dbusservice[
                            "/Balances/Cell%s" % (str(i + 1))
                        ] = self.battery.get_cell_balancing(i)
                    if voltage:
                        voltage_sum += voltage
                pathbase = (
                    "Cell" if (utils.BATTERY_CELL_DATA_FORMAT & 2) else "Voltages"
                )
                self._dbusservice["/%s/Sum" % pathbase] = voltage_sum
                self._dbusservice["/%s/Diff" % pathbase] = (
                    self.battery.get_max_cell_voltage()
                    - self.battery.get_min_cell_voltage()
                )
            except Exception:
                pass

        # Update TimeToGo and/or TimeToSoC
        try:
            # calculate current average for the last 300 cycles
            # if Time-To-Go or Time-To-SoC is enabled
            if utils.TIME_TO_GO_ENABLE or len(utils.TIME_TO_SOC_POINTS) > 0:
                if self.battery.current is not None:
                    self.battery.current_avg_lst.append(self.battery.current)

                # delete oldest value
                if len(self.battery.current_avg_lst) > 300:
                    del self.battery.current_avg_lst[0]

            """
            logger.info(
                str(self.battery.capacity)
                + " - "
                + str(utils.TIME_TO_GO_ENABLE)
                + " - "
                + str(len(utils.TIME_TO_SOC_POINTS))
                + " - "
                + str(int(time()) - self.battery.time_to_soc_update)
                + " - "
                + str(utils.TIME_TO_SOC_RECALCULATE_EVERY)
            )
            """

            if (
                self.battery.capacity is not None
                and (utils.TIME_TO_GO_ENABLE or len(utils.TIME_TO_SOC_POINTS) > 0)
                and (
                    int(time()) - self.battery.time_to_soc_update
                    >= utils.TIME_TO_SOC_RECALCULATE_EVERY
                )
            ):
                self.battery.time_to_soc_update = int(time())

                self.battery.current_avg = round(
                    sum(self.battery.current_avg_lst)
                    / len(self.battery.current_avg_lst),
                    2,
                )

                self._dbusservice["/CurrentAvg"] = self.battery.current_avg

                percent_per_seconds = (
                    abs(self.battery.current_avg / (self.battery.capacity / 100)) / 3600
                )

                # Update TimeToGo item
                if utils.TIME_TO_GO_ENABLE and percent_per_seconds is not None:
                    # Update TimeToGo item, has to be a positive int since it's used from dbus-systemcalc-py
                    time_to_go = self.battery.get_timeToSoc(
                        # switch value depending on charging/discharging
                        utils.SOC_LOW_WARNING if self.battery.current_avg < 0 else 100,
                        percent_per_seconds,
                        True,
                    )

                    # Check that time_to_go is not None and current is not near zero
                    self._dbusservice["/TimeToGo"] = (
                        abs(int(time_to_go))
                        if time_to_go is not None
                        and abs(self.battery.current_avg) > 0.1
                        else None
                    )

                # Update TimeToSoc items
                if len(utils.TIME_TO_SOC_POINTS) > 0:
                    for num in utils.TIME_TO_SOC_POINTS:
                        self._dbusservice["/TimeToSoC/" + str(num)] = (
                            self.battery.get_timeToSoc(num, percent_per_seconds)
                            if self.battery.current_avg
                            else None
                        )

        except Exception:
            exception_type, exception_object, exception_traceback = sys.exc_info()
            file = exception_traceback.tb_frame.f_code.co_filename
            line = exception_traceback.tb_lineno
            logger.error(
                f"Exception occurred: {repr(exception_object)} of type {exception_type} in {file} line #{line}"
            )
            pass

        # save settings every 15 seconds to dbus
        if int(time()) % 15:
            self.saveBatteryOptions()

        if self.battery.soc is not None:
            logger.debug("logged to dbus [%s]" % str(round(self.battery.soc, 2)))
            self.battery.log_cell_data()

        if self.battery.has_settings:
            self._dbusservice["/Settings/ResetSoc"] = self.battery.reset_soc

    def getSettingsWithValues(
        self, bus, service: str, object_path: str, recursive: bool = True
    ) -> dict:
        # print(object_path)
        obj = bus.get_object(service, object_path)
        iface = dbus.Interface(obj, "org.freedesktop.DBus.Introspectable")
        xml_string = iface.Introspect()
        # print(xml_string)
        result = {}
        for child in ElementTree.fromstring(xml_string):
            if child.tag == "node" and recursive:
                if object_path == "/":
                    object_path = ""
                new_path = "/".join((object_path, child.attrib["name"]))
                # result.update(getSettingsWithValues(bus, service, new_path))
                result_sub = self.getSettingsWithValues(bus, service, new_path)
                self.merge_dicts(result, result_sub)
            elif child.tag == "interface":
                if child.attrib["name"] == "com.victronenergy.Settings":
                    settings_iface = dbus.Interface(obj, "com.victronenergy.BusItem")
                    method = settings_iface.get_dbus_method("GetValue")
                    try:
                        value = method()
                        if type(value) is not dbus.Dictionary:
                            # result[object_path] = str(value)
                            self.merge_dicts(
                                result, self.create_nested_dict(object_path, str(value))
                            )
                            # print(f"{object_path}: {value}")
                        if not recursive:
                            return value
                    except dbus.exceptions.DBusException as e:
                        logger.error(
                            f"getSettingsWithValues(): Failed to get value: {e}"
                        )

        return result

    def setSetting(
        self, bus, service: str, object_path: str, setting_name: str, value
    ) -> bool:
        obj = bus.get_object(service, object_path + "/" + setting_name)
        # iface = dbus.Interface(obj, "org.freedesktop.DBus.Introspectable")
        # xml_string = iface.Introspect()
        # print(xml_string)
        settings_iface = dbus.Interface(obj, "com.victronenergy.BusItem")
        method = settings_iface.get_dbus_method("SetValue")
        try:
            logger.debug(f"Setted setting {object_path}/{setting_name} to {value}")
            return True if method(value) == 0 else False
        except dbus.exceptions.DBusException as e:
            logger.error(f"Failed to set setting: {e}")

    def removeSetting(
        self, bus, service: str, object_path: str, setting_name: list
    ) -> bool:
        obj = bus.get_object(service, object_path)
        # iface = dbus.Interface(obj, "org.freedesktop.DBus.Introspectable")
        # xml_string = iface.Introspect()
        # print(xml_string)
        settings_iface = dbus.Interface(obj, "com.victronenergy.Settings")
        method = settings_iface.get_dbus_method("RemoveSettings")
        try:
            logger.debug(f"Removed setting at {object_path}")
            return True if method(setting_name) == 0 else False
        except dbus.exceptions.DBusException as e:
            logger.error(f"Failed to remove setting: {e}")

    def create_nested_dict(self, path, value) -> dict:
        keys = path.strip("/").split("/")
        result = current = {}
        for key in keys[:-1]:
            current[key] = {}
            current = current[key]
        current[keys[-1]] = value
        return result

    def merge_dicts(self, dict1, dict2) -> None:
        for key in dict2:
            if (
                key in dict1
                and isinstance(dict1[key], dict)
                and isinstance(dict2[key], dict)
            ):
                self.merge_dicts(dict1[key], dict2[key])
            else:
                dict1[key] = dict2[key]

    # save custom name to dbus
    def custom_name_callback(self, path, value) -> str:
        result = self.setSetting(
            get_bus(),
            "com.victronenergy.settings",
            self.path_battery,
            "CustomName",
            value,
        )
        logger.debug(
            f'CustomName changed to "{value}" for {self.path_battery}: {result}'
        )
        return value if result else None

    # save battery options to dbus
    def saveBatteryOptions(self) -> bool:
        result = True

        if (
            self.battery.allow_max_voltage
            != self.save_charge_details_last["allow_max_voltage"]
        ):
            self.save_charge_details_last[
                "allow_max_voltage"
            ] = self.battery.allow_max_voltage
            result = result + self.setSetting(
                get_bus(),
                "com.victronenergy.settings",
                self.path_battery,
                "AllowMaxVoltage",
                1 if self.battery.allow_max_voltage else 0,
            )
            logger.info(
                f"Saved AllowMaxVoltage. Before {self.save_charge_details_last['allow_max_voltage']}, "
                + f"after {self.battery.allow_max_voltage}"
            )

        if (
            self.battery.max_voltage_start_time
            != self.save_charge_details_last["max_voltage_start_time"]
        ):
            self.save_charge_details_last[
                "max_voltage_start_time"
            ] = self.battery.max_voltage_start_time
            result = result and self.setSetting(
                get_bus(),
                "com.victronenergy.settings",
                self.path_battery,
                "MaxVoltageStartTime",
                self.battery.max_voltage_start_time
                if self.battery.max_voltage_start_time is not None
                else "",
            )
            logger.info(
                f"Saved MaxVoltageStartTime. Before {self.save_charge_details_last['max_voltage_start_time']}, "
                + f"after {self.battery.max_voltage_start_time}"
            )

        if self.battery.soc_calc != self.save_charge_details_last["soc_calc"]:
            self.save_charge_details_last["soc_calc"] = self.battery.soc_calc
            result = result and self.setSetting(
                get_bus(),
                "com.victronenergy.settings",
                self.path_battery,
                "SocCalc",
                self.battery.soc_calc,
            )
            logger.debug(f"soc_calc written to dbus: {self.battery.soc_calc}")

        if (
            self.battery.soc_reset_last_reached
            != self.save_charge_details_last["soc_reset_last_reached"]
        ):
            self.save_charge_details_last[
                "soc_reset_last_reached"
            ] = self.battery.soc_reset_last_reached
            result = result and self.setSetting(
                get_bus(),
                "com.victronenergy.settings",
                self.path_battery,
                "SocResetLastReached",
                self.battery.soc_reset_last_reached,
            )
            logger.info(
                f"Saved SocResetLastReached. Before {self.save_charge_details_last['soc_reset_last_reached']}, "
                + f"after {self.battery.soc_reset_last_reached}",
            )

        return result
