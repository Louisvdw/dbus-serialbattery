# -*- coding: utf-8 -*-
from typing import Union, Tuple, List, Callable

from utils import logger
import utils
import logging
import math
from time import time
from abc import ABC, abstractmethod
import re
import sys


class Protection(object):
    """
    This class holds Warning and alarm states for different types of Checks
    They are of type integer, 2 represents an Alarm, 1 a Warning, 0 if everything is fine
    """

    ALARM = 2
    WARNING = 1
    OK = 0

    def __init__(self):
        self.voltage_high: int = None
        self.voltage_low: int = None
        self.voltage_cell_low: int = None
        self.soc_low: int = None
        self.current_over: int = None
        self.current_under: int = None
        self.cell_imbalance: int = None
        self.internal_failure: int = None
        self.temp_high_charge: int = None
        self.temp_low_charge: int = None
        self.temp_high_discharge: int = None
        self.temp_low_discharge: int = None
        self.temp_high_internal: int = None


class Cell:
    """
    This class holds information about a single Cell
    """

    voltage = None
    balance = None
    temp = None

    def __init__(self, balance):
        self.balance = balance


class Battery(ABC):
    """
    This Class is the abstract baseclass for all batteries. For each BMS this class needs to be extended
    and the abstract methods need to be implemented. The main program in dbus-serialbattery.py will then
    use the individual implementations as type Battery and work with it.
    """

    def __init__(self, port, baud, address):
        self.port = port
        self.baud_rate = baud
        self.role = "battery"
        self.type = "Generic"
        self.poll_interval = 1000
        self.online = True
        self.hardware_version = None
        self.cell_count = None
        # max battery charge/discharge current
        self.max_battery_charge_current = None
        self.max_battery_discharge_current = None
        self.has_settings = 0

        # fetched from the BMS from a field where the user can input a custom string
        # only if available
        self.custom_field = None

        self.init_values()

    def init_values(self):
        """
        Used to reset values, if battery unexpectly disconnects
        """
        self.voltage = None
        self.current = None
        self.capacity_remain = None
        self.capacity = None
        self.cycles = None
        self.total_ah_drawn = None
        self.production = None
        self.protection = Protection()
        self.version = None
        self.soc = None
        self.time_to_soc_update = 0
        self.charge_fet = None
        self.discharge_fet = None
        self.balance_fet = None
        self.temp_sensors = None
        self.temp1 = None
        self.temp2 = None
        self.temp3 = None
        self.temp4 = None
        self.temp_mos = None
        self.cells: List[Cell] = []
        self.control_charging = None
        self.control_voltage = None
        self.max_battery_voltage = None
        self.min_battery_voltage = None
        self.allow_max_voltage = True
        self.max_voltage_start_time = None
        self.transition_start_time = None
        self.control_voltage_at_transition_start = None
        self.charge_mode = None
        self.charge_mode_debug = ""
        self.charge_limitation = None
        self.discharge_limitation = None
        self.linear_cvl_last_set = 0
        self.linear_ccl_last_set = 0
        self.linear_dcl_last_set = 0
        self.control_current = None
        self.control_previous_total = None
        self.control_previous_max = None
        self.control_discharge_current = None
        self.control_charge_current = None
        self.control_allow_charge = None
        self.control_allow_discharge = None

    @abstractmethod
    def test_connection(self) -> bool:
        """
        This abstract method needs to be implemented for each BMS. It shoudl return true if a connection
        to the BMS can be established, false otherwise.
        :return: the success state
        """
        # Each driver must override this function to test if a connection can be made
        # return false when failed, true if successful
        return False

    def unique_identifier(self) -> str:
        """
        Used to identify a BMS when multiple BMS are connected
        If not provided by the BMS/driver then the hardware version and capacity is used,
        since it can be changed by small amounts to make a battery unique.
        On +/- 5 Ah you can identify 11 batteries
        """
        string = (
            "".join(filter(str.isalnum, str(self.hardware_version))) + "_"
            if self.hardware_version is not None and self.hardware_version != ""
            else ""
        )
        string += str(self.capacity) + "Ah"
        return string

    def connection_name(self) -> str:
        return "Serial " + self.port

    def custom_name(self) -> str:
        """
        Check if the custom name is present in the config file, else return default name
        """
        if len(utils.CUSTOM_BATTERY_NAMES) > 0:
            for name in utils.CUSTOM_BATTERY_NAMES:
                tmp = name.split(":")
                if tmp[0].strip() == self.port:
                    return tmp[1].strip()
        else:
            return "SerialBattery(" + self.type + ")"

    def product_name(self) -> str:
        return "SerialBattery(" + self.type + ")"

    @abstractmethod
    def get_settings(self) -> bool:
        """
        Each driver must override this function to read/set the battery settings
        It is called once after a successful connection by DbusHelper.setup_vedbus()
        Values:  battery_type, version, hardware_version, min_battery_voltage, max_battery_voltage,
        MAX_BATTERY_CHARGE_CURRENT, MAX_BATTERY_DISCHARGE_CURRENT, cell_count, capacity

        :return: false when fail, true if successful
        """
        return False

    def use_callback(self, callback: Callable) -> bool:
        """
        Each driver may override this function to indicate whether it is
        able to provide value updates on its own.

        :return: false when battery cannot provide updates by itself and will be polled
                 every poll_interval milliseconds for new values
                 true if callable should be used for updates as they arrive from the battery
        """
        return False

    @abstractmethod
    def refresh_data(self) -> bool:
        """
        Each driver must override this function to read battery data and populate this class
        It is called each poll just before the data is published to vedbus

        :return:  false when fail, true if successful
        """
        return False

    def to_temp(self, sensor: int, value: float) -> None:
        """
        Keep the temp value between -20 and 100 to handle sensor issues or no data.
        The BMS should have already protected before those limits have been reached.

        :param sensor: temperature sensor number
        :param value: the sensor value
        :return:
        """
        if sensor == 0:
            self.temp_mos = min(max(value, -20), 100)
        if sensor == 1:
            self.temp1 = min(max(value, -20), 100)
        if sensor == 2:
            self.temp2 = min(max(value, -20), 100)
        if sensor == 3:
            self.temp3 = min(max(value, -20), 100)
        if sensor == 4:
            self.temp4 = min(max(value, -20), 100)

    def manage_charge_voltage(self) -> None:
        """
        manages the charge voltage by setting self.control_voltage
        :return: None
        """
        self.prepare_voltage_management()
        if utils.CVCM_ENABLE:
            if utils.LINEAR_LIMITATION_ENABLE:
                self.manage_charge_voltage_linear()
            else:
                self.manage_charge_voltage_step()
        # on CVCM_ENABLE = False apply max voltage
        else:
            self.control_voltage = round(self.max_battery_voltage, 3)
            self.charge_mode = "Keep always max voltage"

    def prepare_voltage_management(self) -> None:
        self.max_battery_voltage = utils.MAX_CELL_VOLTAGE * self.cell_count
        self.min_battery_voltage = utils.MIN_CELL_VOLTAGE * self.cell_count

    def manage_charge_voltage_linear(self) -> None:
        """
        manages the charge voltage using linear interpolation by setting self.control_voltage
        :return: None
        """
        foundHighCellVoltage = False
        voltageSum = 0
        penaltySum = 0
        tDiff = 0
        current_time = int(time())
        # meassurment and variation tolerance in volts
        measurementToleranceVariation = 0.022
        
        try:
            # calculate battery sum
            for i in range(self.cell_count):
                voltage = self.get_cell_voltage(i)
                if voltage:
                    voltageSum += voltage

                    # calculate penalty sum to prevent single cell overcharge by using current cell voltage
                    if voltage > utils.MAX_CELL_VOLTAGE:
                        # foundHighCellVoltage: reset to False is not needed, since it is recalculated every second
                        foundHighCellVoltage = True
                        penaltySum += voltage - utils.MAX_CELL_VOLTAGE

            voltageDiff = self.get_max_cell_voltage() - self.get_min_cell_voltage()

            if self.max_voltage_start_time is None:
                # start timer, if max voltage is reached and cells are balanced
                if (
                    self.max_battery_voltage - utils.VOLTAGE_DROP <= voltageSum
                    and voltageDiff <= utils.CELL_VOLTAGE_DIFF_KEEP_MAX_VOLTAGE_UNTIL
                    and self.allow_max_voltage
                ):
                    self.max_voltage_start_time = current_time

                # allow max voltage again, if cells are unbalanced or SoC threshold is reached
                elif (
                    utils.SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT > self.soc
                    or voltageDiff >= utils.CELL_VOLTAGE_DIFF_TO_RESET_VOLTAGE_LIMIT
                ) and not self.allow_max_voltage:
                    self.allow_max_voltage = True
                else:
                    pass

            else:
                tDiff = current_time - self.max_voltage_start_time
                # keep max voltage for MAX_VOLTAGE_TIME_SEC more seconds
                if utils.MAX_VOLTAGE_TIME_SEC < tDiff:
                    self.allow_max_voltage = False
                    self.max_voltage_start_time = None
                    if self.soc <= utils.SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT:
                        # write to log, that reset to float was not possible
                        logger.error(
                            f"Could not change to float voltage. Battery SoC ({self.soc}%) is lower"
                            + f" than SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT ({utils.SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT}%)."
                            + " Please reset SoC manually or lower the SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT in the"
                            + ' "config.ini".'
                        )

                # we don't forget to reset max_voltage_start_time wenn we going to bulk(dynamic) mode
                # regardless of whether we were in absorption mode or not
                if (
                    voltageSum
                    < self.max_battery_voltage
                    - utils.VOLTAGE_DROP
                    - measurementToleranceVariation
                ):
                    self.max_voltage_start_time = None

            # INFO: battery will only switch to Absorption, if all cells are balanced.
            #       Reach MAX_CELL_VOLTAGE * cell count if they are all balanced.
            if foundHighCellVoltage and self.allow_max_voltage:
                # Keep penalty above min battery voltage and below max battery voltage
                control_voltage = round(
                    min(
                        max(
                            voltageSum - penaltySum,
                            self.min_battery_voltage,
                        ),
                        self.max_battery_voltage,
                    ),
                    3,
                )
                self.set_cvl_linear(control_voltage)

                self.charge_mode = (
                    "Bulk dynamic"
                    if self.max_voltage_start_time is None
                    else "Absorption dynamic"
                )

            elif self.allow_max_voltage:
                self.control_voltage = round(self.max_battery_voltage, 3)
                self.charge_mode = (
                    # "Bulk" if self.max_voltage_start_time is None else "Absorption"
                    "Bulk"
                    if self.max_voltage_start_time is None
                    else "Absorption"
                )

            else:
                floatVoltage = round((utils.FLOAT_CELL_VOLTAGE * self.cell_count), 3)
                chargeMode = "Float"
                if self.control_voltage:
                    if not self.charge_mode.startswith("Float"):
                        self.transition_start_time = current_time
                        self.initial_control_voltage = self.control_voltage
                        chargeMode = "Float Transition"
                    elif self.charge_mode.startswith("Float Transition"):
                        elapsed_time = current_time - self.transition_start_time
                        # Voltage reduction per second
                        VOLTAGE_REDUCTION_PER_SECOND = 0.01 / 10
                        voltage_reduction = min(
                            VOLTAGE_REDUCTION_PER_SECOND * elapsed_time,
                            self.initial_control_voltage - floatVoltage,
                        )
                        self.set_cvl_linear(
                            self.initial_control_voltage - voltage_reduction
                        )
                        if self.control_voltage <= floatVoltage:
                            self.control_voltage = floatVoltage
                            chargeMode = "Float"
                        else:
                            chargeMode = "Float Transition"
                else:
                    self.control_voltage = floatVoltage
                self.charge_mode = chargeMode

            if (
                self.allow_max_voltage
                and self.get_balancing()
                and voltageDiff >= utils.CELL_VOLTAGE_DIFF_TO_RESET_VOLTAGE_LIMIT
            ):
                self.charge_mode += " + Balancing"

            self.charge_mode += " (Linear Mode)"

            # uncomment for enabling debugging infos in GUI
            """
            self.charge_mode_debug = (
                f"max_battery_voltage: {round(self.max_battery_voltage, 2)}V"
            )
            self.charge_mode_debug += (
                f" - VOLTAGE_DROP: {round(utils.VOLTAGE_DROP, 2)}V"
            )
            self.charge_mode_debug += f"\nvoltageSum: {round(voltageSum, 2)}V"
            self.charge_mode_debug += f" • voltageDiff: {round(voltageDiff, 3)}V"
            self.charge_mode_debug += (
                f"\ncontrol_voltage: {round(self.control_voltage, 2)}V"
            )
            self.charge_mode_debug += f" • penaltySum: {round(penaltySum, 3)}V"
            self.charge_mode_debug += f"\ntDiff: {tDiff}/{utils.MAX_VOLTAGE_TIME_SEC}"
            self.charge_mode_debug += f" • SoC: {self.soc}%"
            self.charge_mode_debug += (
                f" • Reset SoC: {utils.SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT}%"
            )
            self.charge_mode_debug += f"\nallow_max_voltage: {self.allow_max_voltage}"
            self.charge_mode_debug += (
                f"\nmax_voltage_start_time: {self.max_voltage_start_time}"
            )
            self.charge_mode_debug += f"\ncurrent_time: {current_time}"
            self.charge_mode_debug += (
                f"\nlinear_cvl_last_set: {self.linear_cvl_last_set}"
            )
            """

        except TypeError:
            self.control_voltage = None
            self.charge_mode = "--"

    def set_cvl_linear(self, control_voltage) -> bool:
        """
        set CVL only once every LINEAR_RECALCULATION_EVERY seconds
        :return: bool
        """
        current_time = int(time())
        if utils.LINEAR_RECALCULATION_EVERY <= current_time - self.linear_cvl_last_set:
            self.control_voltage = control_voltage
            self.linear_cvl_last_set = current_time
            return True
        return False

    def manage_charge_voltage_step(self) -> None:
        """
        manages the charge voltage using a step function by setting self.control_voltage
        :return: None
        """
        voltageSum = 0
        tDiff = 0

        try:
            # calculate battery sum
            for i in range(self.cell_count):
                voltage = self.get_cell_voltage(i)
                if voltage:
                    voltageSum += voltage

            if self.max_voltage_start_time is None:
                # check if max voltage is reached and start timer to keep max voltage
                if (
                    self.max_battery_voltage - utils.VOLTAGE_DROP <= voltageSum
                    and self.allow_max_voltage
                ):
                    # example 2
                    self.max_voltage_start_time = time()

                # check if reset soc is greater than battery soc
                # this prevents flapping between max and float voltage
                elif (
                    utils.SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT > self.soc
                    and not self.allow_max_voltage
                ):
                    self.allow_max_voltage = True

                # do nothing
                else:
                    pass

            # timer started
            else:
                tDiff = time() - self.max_voltage_start_time
                if utils.MAX_VOLTAGE_TIME_SEC < tDiff:
                    self.allow_max_voltage = False
                    self.max_voltage_start_time = None

                else:
                    pass

            if self.allow_max_voltage:
                self.control_voltage = self.max_battery_voltage
                self.charge_mode = (
                    "Bulk" if self.max_voltage_start_time is None else "Absorption"
                )

            else:
                self.control_voltage = utils.FLOAT_CELL_VOLTAGE * self.cell_count
                self.charge_mode = "Float"

            self.charge_mode += " (Step Mode)"

        except TypeError:
            self.control_voltage = None
            self.charge_mode = "--"

    def manage_charge_current(self) -> None:
        # Manage Charge Current Limitations
        charge_limits = {utils.MAX_BATTERY_CHARGE_CURRENT: "Config Limit"}

        # if values are not the same, then the limit was read also from the BMS
        if utils.MAX_BATTERY_CHARGE_CURRENT != self.max_battery_charge_current:
            charge_limits.update({self.max_battery_charge_current: "BMS Limit"})

        if utils.CCCM_CV_ENABLE:
            tmp = self.calcMaxChargeCurrentReferringToCellVoltage()
            if self.max_battery_charge_current != tmp:
                if tmp in charge_limits:
                    charge_limits.update({tmp: charge_limits[tmp] + ", Cell Voltage"})
                else:
                    charge_limits.update({tmp: "Cell Voltage"})

        if utils.CCCM_T_ENABLE:
            tmp = self.calcMaxChargeCurrentReferringToTemperature()
            if self.max_battery_charge_current != tmp:
                if tmp in charge_limits:
                    charge_limits.update({tmp: charge_limits[tmp] + ", Temp"})
                else:
                    charge_limits.update({tmp: "Temp"})

        if utils.CCCM_SOC_ENABLE:
            tmp = self.calcMaxChargeCurrentReferringToSoc()
            if self.max_battery_charge_current != tmp:
                if tmp in charge_limits:
                    charge_limits.update({tmp: charge_limits[tmp] + ", SoC"})
                else:
                    charge_limits.update({tmp: "SoC"})

        # do not set CCL immediately, but only
        # - after LINEAR_RECALCULATION_EVERY passed
        # - if CCL changes to 0
        # - if CCL changes more than LINEAR_RECALCULATION_ON_PERC_CHANGE
        ccl = round(min(charge_limits), 3)  # gets changed after finished testing
        diff = (
            abs(self.control_charge_current - ccl)
            if self.control_charge_current is not None
            else 0
        )
        if (
            int(time()) - self.linear_ccl_last_set >= utils.LINEAR_RECALCULATION_EVERY
            or ccl == 0
            or (
                diff
                >= self.control_charge_current
                * utils.LINEAR_RECALCULATION_ON_PERC_CHANGE
                / 100
            )
        ):
            self.linear_ccl_last_set = int(time())

            self.control_charge_current = ccl

            self.charge_limitation = charge_limits[min(charge_limits)]

        if self.control_charge_current == 0:
            self.control_allow_charge = False
        else:
            self.control_allow_charge = True

        #####

        # Manage Discharge Current Limitations
        discharge_limits = {utils.MAX_BATTERY_DISCHARGE_CURRENT: "Config Limit"}

        # if values are not the same, then the limit was read also from the BMS
        if utils.MAX_BATTERY_DISCHARGE_CURRENT != self.max_battery_discharge_current:
            discharge_limits.update({self.max_battery_discharge_current: "BMS Limit"})

        if utils.DCCM_CV_ENABLE:
            tmp = self.calcMaxDischargeCurrentReferringToCellVoltage()
            if self.max_battery_discharge_current != tmp:
                if tmp in discharge_limits:
                    discharge_limits.update(
                        {tmp: discharge_limits[tmp] + ", Cell Voltage"}
                    )
                else:
                    discharge_limits.update({tmp: "Cell Voltage"})

        if utils.DCCM_T_ENABLE:
            tmp = self.calcMaxDischargeCurrentReferringToTemperature()
            if self.max_battery_discharge_current != tmp:
                if tmp in discharge_limits:
                    discharge_limits.update({tmp: discharge_limits[tmp] + ", Temp"})
                else:
                    discharge_limits.update({tmp: "Temp"})

        if utils.DCCM_SOC_ENABLE:
            tmp = self.calcMaxDischargeCurrentReferringToSoc()
            if self.max_battery_discharge_current != tmp:
                if tmp in discharge_limits:
                    discharge_limits.update({tmp: discharge_limits[tmp] + ", SoC"})
                else:
                    discharge_limits.update({tmp: "SoC"})

        # do not set DCL immediately, but only
        # - after LINEAR_RECALCULATION_EVERY passed
        # - if DCL changes to 0
        # - if DCL changes more than LINEAR_RECALCULATION_ON_PERC_CHANGE
        dcl = round(min(discharge_limits), 3)  # gets changed after finished testing
        diff = (
            abs(self.control_discharge_current - dcl)
            if self.control_discharge_current is not None
            else 0
        )
        if (
            int(time()) - self.linear_dcl_last_set >= utils.LINEAR_RECALCULATION_EVERY
            or dcl == 0
            or (
                diff
                >= self.control_discharge_current
                * utils.LINEAR_RECALCULATION_ON_PERC_CHANGE
                / 100
            )
        ):
            self.linear_dcl_last_set = int(time())

            self.control_discharge_current = dcl

            self.discharge_limitation = discharge_limits[min(discharge_limits)]

        if self.control_discharge_current == 0:
            self.control_allow_discharge = False
        else:
            self.control_allow_discharge = True

    def calcMaxChargeCurrentReferringToCellVoltage(self) -> float:
        try:
            if utils.LINEAR_LIMITATION_ENABLE:
                return utils.calcLinearRelationship(
                    self.get_max_cell_voltage(),
                    utils.CELL_VOLTAGES_WHILE_CHARGING,
                    utils.MAX_CHARGE_CURRENT_CV,
                )
            return utils.calcStepRelationship(
                self.get_max_cell_voltage(),
                utils.CELL_VOLTAGES_WHILE_CHARGING,
                utils.MAX_CHARGE_CURRENT_CV,
                False,
            )
        except Exception:
            return self.max_battery_charge_current

    def calcMaxDischargeCurrentReferringToCellVoltage(self) -> float:
        try:
            if utils.LINEAR_LIMITATION_ENABLE:
                return utils.calcLinearRelationship(
                    self.get_min_cell_voltage(),
                    utils.CELL_VOLTAGES_WHILE_DISCHARGING,
                    utils.MAX_DISCHARGE_CURRENT_CV,
                )
            return utils.calcStepRelationship(
                self.get_min_cell_voltage(),
                utils.CELL_VOLTAGES_WHILE_DISCHARGING,
                utils.MAX_DISCHARGE_CURRENT_CV,
                True,
            )
        except Exception:
            return self.max_battery_charge_current

    def calcMaxChargeCurrentReferringToTemperature(self) -> float:
        if self.get_max_temp() is None:
            return self.max_battery_charge_current

        temps = {0: self.get_max_temp(), 1: self.get_min_temp()}

        for key, currentMaxTemperature in temps.items():
            if utils.LINEAR_LIMITATION_ENABLE:
                temps[key] = utils.calcLinearRelationship(
                    currentMaxTemperature,
                    utils.TEMPERATURE_LIMITS_WHILE_CHARGING,
                    utils.MAX_CHARGE_CURRENT_T,
                )
            else:
                temps[key] = utils.calcStepRelationship(
                    currentMaxTemperature,
                    utils.TEMPERATURE_LIMITS_WHILE_CHARGING,
                    utils.MAX_CHARGE_CURRENT_T,
                    False,
                )

        return min(temps[0], temps[1])

    def calcMaxDischargeCurrentReferringToTemperature(self) -> float:
        if self.get_max_temp() is None:
            return self.max_battery_discharge_current

        temps = {0: self.get_max_temp(), 1: self.get_min_temp()}

        for key, currentMaxTemperature in temps.items():
            if utils.LINEAR_LIMITATION_ENABLE:
                temps[key] = utils.calcLinearRelationship(
                    currentMaxTemperature,
                    utils.TEMPERATURE_LIMITS_WHILE_DISCHARGING,
                    utils.MAX_DISCHARGE_CURRENT_T,
                )
            else:
                temps[key] = utils.calcStepRelationship(
                    currentMaxTemperature,
                    utils.TEMPERATURE_LIMITS_WHILE_DISCHARGING,
                    utils.MAX_DISCHARGE_CURRENT_T,
                    True,
                )

        return min(temps[0], temps[1])

    def calcMaxChargeCurrentReferringToSoc(self) -> float:
        try:
            # Create value list. Will more this to the settings object
            SOC_WHILE_CHARGING = [
                100,
                utils.CC_SOC_LIMIT1,
                utils.CC_SOC_LIMIT2,
                utils.CC_SOC_LIMIT3,
            ]
            MAX_CHARGE_CURRENT_SOC = [
                utils.CC_CURRENT_LIMIT1,
                utils.CC_CURRENT_LIMIT2,
                utils.CC_CURRENT_LIMIT3,
                utils.MAX_BATTERY_CHARGE_CURRENT,
            ]
            if utils.LINEAR_LIMITATION_ENABLE:
                return utils.calcLinearRelationship(
                    self.soc, SOC_WHILE_CHARGING, MAX_CHARGE_CURRENT_SOC
                )
            return utils.calcStepRelationship(
                self.soc, SOC_WHILE_CHARGING, MAX_CHARGE_CURRENT_SOC, True
            )
        except Exception:
            return self.max_battery_charge_current

    def calcMaxDischargeCurrentReferringToSoc(self) -> float:
        try:
            # Create value list. Will more this to the settings object
            SOC_WHILE_DISCHARGING = [
                utils.DC_SOC_LIMIT3,
                utils.DC_SOC_LIMIT2,
                utils.DC_SOC_LIMIT1,
            ]
            MAX_DISCHARGE_CURRENT_SOC = [
                utils.MAX_BATTERY_DISCHARGE_CURRENT,
                utils.DC_CURRENT_LIMIT3,
                utils.DC_CURRENT_LIMIT2,
                utils.DC_CURRENT_LIMIT1,
            ]
            if utils.LINEAR_LIMITATION_ENABLE:
                return utils.calcLinearRelationship(
                    self.soc, SOC_WHILE_DISCHARGING, MAX_DISCHARGE_CURRENT_SOC
                )
            return utils.calcStepRelationship(
                self.soc, SOC_WHILE_DISCHARGING, MAX_DISCHARGE_CURRENT_SOC, True
            )
        except Exception:
            return self.max_battery_charge_current

    def get_min_cell(self) -> int:
        min_voltage = 9999
        min_cell = None
        if len(self.cells) == 0 and hasattr(self, "cell_min_no"):
            return self.cell_min_no

        for c in range(min(len(self.cells), self.cell_count)):
            if (
                self.cells[c].voltage is not None
                and min_voltage > self.cells[c].voltage
            ):
                min_voltage = self.cells[c].voltage
                min_cell = c
        return min_cell

    def get_max_cell(self) -> int:
        max_voltage = 0
        max_cell = None
        if len(self.cells) == 0 and hasattr(self, "cell_max_no"):
            return self.cell_max_no

        for c in range(min(len(self.cells), self.cell_count)):
            if (
                self.cells[c].voltage is not None
                and max_voltage < self.cells[c].voltage
            ):
                max_voltage = self.cells[c].voltage
                max_cell = c
        return max_cell

    def get_min_cell_desc(self) -> Union[str, None]:
        cell_no = self.get_min_cell()
        return cell_no if cell_no is None else "C" + str(cell_no + 1)

    def get_max_cell_desc(self) -> Union[str, None]:
        cell_no = self.get_max_cell()
        return cell_no if cell_no is None else "C" + str(cell_no + 1)

    def get_cell_voltage(self, idx) -> Union[float, None]:
        if idx >= min(len(self.cells), self.cell_count):
            return None
        return self.cells[idx].voltage

    def get_cell_balancing(self, idx) -> Union[int, None]:
        if idx >= min(len(self.cells), self.cell_count):
            return None
        if self.cells[idx].balance is not None and self.cells[idx].balance:
            return 1
        return 0

    def get_capacity_remain(self) -> Union[float, None]:
        if self.capacity_remain is not None:
            return self.capacity_remain
        if self.capacity is not None and self.soc is not None:
            return self.capacity * self.soc / 100
        return None

    def get_timeToSoc(self, socnum, crntPrctPerSec, onlyNumber=False) -> str:
        if self.current > 0:
            diffSoc = socnum - self.soc
        else:
            diffSoc = self.soc - socnum

        ttgStr = None
        if self.soc != socnum and (diffSoc > 0 or utils.TIME_TO_SOC_INC_FROM is True):
            secondstogo = int(diffSoc / crntPrctPerSec)
            ttgStr = ""

            if onlyNumber or utils.TIME_TO_SOC_VALUE_TYPE & 1:
                ttgStr += str(secondstogo)
                if not onlyNumber and utils.TIME_TO_SOC_VALUE_TYPE & 2:
                    ttgStr += " ["
            if not onlyNumber and utils.TIME_TO_SOC_VALUE_TYPE & 2:
                ttgStr += self.get_secondsToString(secondstogo)

                if utils.TIME_TO_SOC_VALUE_TYPE & 1:
                    ttgStr += "]"

        return ttgStr

    def get_secondsToString(self, timespan, precision=3) -> str:
        """
        Transforms seconds to a string in the format: 1d 1h 1m 1s (Victron Style)
        :param precision:
        0 = 1d
        1 = 1d 1h
        2 = 1d 1h 1m
        3 = 1d 1h 1m 1s

        This was added, since timedelta() returns strange values, if time is negative
        e.g.: seconds: -70245
              --> timedelta output: -1 day, 4:29:15
              --> calculation: -1 day + 4:29:15
              --> real value -19:30:45
        """
        tmp = "" if timespan >= 0 else "-"
        timespan = abs(timespan)

        m, s = divmod(timespan, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)

        tmp += (str(d) + "d ") if d > 0 else ""
        tmp += (str(h) + "h ") if precision >= 1 and h > 0 else ""
        tmp += (str(m) + "m ") if precision >= 2 and m > 0 else ""
        tmp += (str(s) + "s ") if precision == 3 and s > 0 else ""

        return tmp.rstrip()

    def get_min_cell_voltage(self) -> Union[float, None]:
        min_voltage = None
        if hasattr(self, "cell_min_voltage"):
            min_voltage = self.cell_min_voltage

        if min_voltage is None:
            try:
                min_voltage = min(
                    c.voltage for c in self.cells if c.voltage is not None
                )
            except ValueError:
                pass
        return min_voltage

    def get_max_cell_voltage(self) -> Union[float, None]:
        max_voltage = None
        if hasattr(self, "cell_max_voltage"):
            max_voltage = self.cell_max_voltage

        if max_voltage is None:
            try:
                max_voltage = max(
                    c.voltage for c in self.cells if c.voltage is not None
                )
            except ValueError:
                pass
        return max_voltage

    def get_midvoltage(self) -> Tuple[Union[float, None], Union[float, None]]:
        """
        This method returns the Voltage "in the middle of the battery"
        as well as a deviation of an ideally balanced battery. It does so by calculating the sum of the first half
        of the cells and adding 1/2 of the "middle cell" voltage (if it exists)
        :return: a tuple of the voltage in the middle, as well as a percentage deviation (total_voltage / 2)
        """
        if (
            not utils.MIDPOINT_ENABLE
            or self.cell_count is None
            or self.cell_count == 0
            or self.cell_count < 4
            or len(self.cells) != self.cell_count
        ):
            return None, None

        halfcount = int(math.floor(self.cell_count / 2))
        uneven_cells_offset = self.cell_count % 2
        half1voltage = 0
        half2voltage = 0

        try:
            half1voltage = sum(
                cell.voltage
                for cell in self.cells[:halfcount]
                if cell.voltage is not None
            )
            half2voltage = sum(
                cell.voltage
                for cell in self.cells[halfcount + uneven_cells_offset :]
                if cell.voltage is not None
            )
        except ValueError:
            pass

        try:
            extra = 0 if self.cell_count % 2 == 0 else self.cells[halfcount].voltage / 2
            # get the midpoint of the battery
            midpoint = half1voltage + extra
            return (
                abs(midpoint),
                abs(
                    (half2voltage - half1voltage) / (half2voltage + half1voltage) * 100
                ),
            )
        except ValueError:
            return None, None

    def get_balancing(self) -> int:
        for c in range(min(len(self.cells), self.cell_count)):
            if self.cells[c].balance is not None and self.cells[c].balance:
                return 1
        return 0

    def get_temperatures(self) -> Union[List[float], None]:
        temperatures = [self.temp1, self.temp2, self.temp3, self.temp4]
        result = [(t, i) for (t, i) in enumerate(temperatures) if t is not None]
        if not result:
            return None

    def get_temp(self) -> Union[float, None]:
        try:
            if utils.TEMP_BATTERY == 1:
                return self.temp1
            elif utils.TEMP_BATTERY == 2:
                return self.temp2
            elif utils.TEMP_BATTERY == 3:
                return self.temp3
            elif utils.TEMP_BATTERY == 4:
                return self.temp4
            else:
                temps = [
                    t
                    for t in [self.temp1, self.temp2, self.temp3, self.temp4]
                    if t is not None
                ]
                n = len(temps)
                if not temps or n == 0:
                    return None
                data = sorted(temps)
                if n % 2 == 1:
                    return data[n // 2]
                else:
                    i = n // 2
                    return (data[i - 1] + data[i]) / 2
        except TypeError:
            return None

    def get_min_temp(self) -> Union[float, None]:
        try:
            temps = [
                t
                for t in [self.temp1, self.temp2, self.temp3, self.temp4]
                if t is not None
            ]
            if not temps:
                return None
            return min(temps)
        except TypeError:
            return None

    def get_min_temp_id(self) -> Union[str, None]:
        try:
            temps = [
                (t, i)
                for i, t in enumerate([self.temp1, self.temp2, self.temp3, self.temp4])
                if t is not None
            ]
            if not temps:
                return None
            index = min(temps)[1]
            if index == 0:
                return utils.TEMP_1_NAME
            if index == 1:
                return utils.TEMP_2_NAME
            if index == 2:
                return utils.TEMP_3_NAME
            if index == 3:
                return utils.TEMP_4_NAME
        except TypeError:
            return None

    def get_max_temp(self) -> Union[float, None]:
        try:
            temps = [
                t
                for t in [self.temp1, self.temp2, self.temp3, self.temp4]
                if t is not None
            ]
            if not temps:
                return None
            return max(temps)
        except TypeError:
            return None

    def get_max_temp_id(self) -> Union[str, None]:
        try:
            temps = [
                (t, i)
                for i, t in enumerate([self.temp1, self.temp2, self.temp3, self.temp4])
                if t is not None
            ]
            if not temps:
                return None
            index = max(temps)[1]
            if index == 0:
                return utils.TEMP_1_NAME
            if index == 1:
                return utils.TEMP_2_NAME
            if index == 2:
                return utils.TEMP_3_NAME
            if index == 3:
                return utils.TEMP_4_NAME
        except TypeError:
            return None

    def get_mos_temp(self) -> Union[float, None]:
        if self.temp_mos is not None:
            return self.temp_mos
        else:
            return None

    def validate_data(self) -> bool:
        """
        Used to validate the data received from the BMS.
        If the data is in the thresholds return True,
        else return False since it's very probably not a BMS
        """
        if self.capacity is not None and (self.capacity < 0 or self.capacity > 1000):
            logger.debug(
                "Capacity outside of thresholds (from 0 to 1000): " + str(self.capacity)
            )
            return False
        if self.current is not None and abs(self.current) > 1000:
            logger.debug(
                "Current outside of thresholds (from -1000 to 1000): "
                + str(self.current)
            )
            return False
        if self.voltage is not None and (self.voltage < 0 or self.voltage > 100):
            logger.debug(
                "Voltage outside of thresholds (form 0 to 100): " + str(self.voltage)
            )
            return False
        if self.soc is not None and (self.soc < 0 or self.soc > 100):
            logger.debug("SoC outside of thresholds (from 0 to 100): " + str(self.soc))
            return False

        return True

    def log_cell_data(self) -> bool:
        if logger.getEffectiveLevel() > logging.INFO and len(self.cells) == 0:
            return False

        cell_res = ""
        cell_counter = 1
        for c in self.cells:
            cell_res += "[{0}]{1}V ".format(cell_counter, c.voltage)
            cell_counter = cell_counter + 1
        logger.debug("Cells:" + cell_res)
        return True

    def log_settings(self) -> None:
        cell_counter = len(self.cells)
        logger.info(f"Battery {self.type} connected to dbus from {self.port}")
        logger.info("========== Settings ==========")
        logger.info(
            f"> Connection voltage: {self.voltage}V | Current: {self.current}A | SoC: {self.soc}%"
        )
        logger.info(
            f"> Cell count: {self.cell_count} | Cells populated: {cell_counter}"
        )
        logger.info(f"> LINEAR LIMITATION ENABLE: {utils.LINEAR_LIMITATION_ENABLE}")
        logger.info(
            f"> MAX BATTERY CHARGE CURRENT: {utils.MAX_BATTERY_CHARGE_CURRENT}A | "
            + f"MAX BATTERY DISCHARGE CURRENT: {utils.MAX_BATTERY_DISCHARGE_CURRENT}A"
        )
        if (
            (
                utils.MAX_BATTERY_CHARGE_CURRENT != self.max_battery_charge_current
                or utils.MAX_BATTERY_DISCHARGE_CURRENT
                != self.max_battery_discharge_current
            )
            and self.max_battery_charge_current is not None
            and self.max_battery_discharge_current is not None
        ):
            logger.info(
                f"> MAX BATTERY CHARGE CURRENT: {self.max_battery_charge_current}A | "
                + f"MAX BATTERY DISCHARGE CURRENT: {self.max_battery_discharge_current}A (read from BMS)"
            )
        logger.info(f"> CVCM:     {utils.CVCM_ENABLE}")
        logger.info(
            f"> MIN CELL VOLTAGE: {utils.MIN_CELL_VOLTAGE}V | MAX CELL VOLTAGE: {utils.MAX_CELL_VOLTAGE}V"
        )
        logger.info(
            f"> CCCM CV:  {str(utils.CCCM_CV_ENABLE).ljust(5)} | DCCM CV:  {utils.DCCM_CV_ENABLE}"
        )
        logger.info(
            f"> CCCM T:   {str(utils.CCCM_T_ENABLE).ljust(5)} | DCCM T:   {utils.DCCM_T_ENABLE}"
        )
        logger.info(
            f"> CCCM SOC: {str(utils.CCCM_SOC_ENABLE).ljust(5)} | DCCM SOC: {utils.DCCM_SOC_ENABLE}"
        )
        logger.info(f"Serial Number/Unique Identifier: {self.unique_identifier()}")

        return

    # save custom name to config file
    def custom_name_callback(self, path, value):
        try:
            if path == "/CustomName":
                file = open(
                    "/data/etc/dbus-serialbattery/" + utils.PATH_CONFIG_USER, "r"
                )
                lines = file.readlines()
                last = len(lines)

                # remove not allowed characters
                value = value.replace(":", "").replace("=", "").replace(",", "").strip()

                # empty string to save new config file
                config_file_new = ""

                # make sure we are in the [DEFAULT] section
                current_line_in_default_section = False
                default_section_checked = False

                # check if already exists
                exists = False

                # count lines
                i = 0
                # looping through the file
                for line in lines:
                    # increment by one
                    i += 1

                    # stripping line break
                    line = line.strip()

                    # check, if current line is after the [DEFAULT] section
                    if line == "[DEFAULT]":
                        current_line_in_default_section = True

                    # check, if current line starts a new section
                    if line != "[DEFAULT]" and re.match(r"^\[.*\]", line):
                        # set default_section_checked to true, if it was already checked and a new section comes on
                        if current_line_in_default_section and not exists:
                            default_section_checked = True
                        current_line_in_default_section = False

                    # check, if the current line is the last line
                    if i == last:
                        default_section_checked = True

                    # insert or replace only in [DEFAULT] section
                    if current_line_in_default_section and re.match(
                        r"^CUSTOM_BATTERY_NAMES.*", line
                    ):
                        # set that the setting was found, else a new one is created
                        exists = True

                        # remove setting name
                        line = re.sub(
                            "^CUSTOM_BATTERY_NAMES\s*=\s*", "", line  # noqa: W605
                        )

                        # change only the name of the current BMS
                        result = []
                        bms_name_list = line.split(",")
                        for bms_name_pair in bms_name_list:
                            tmp = bms_name_pair.split(":")
                            if tmp[0] == self.port:
                                result.append(tmp[0] + ":" + value)
                            else:
                                result.append(bms_name_pair)

                        new_line = "CUSTOM_BATTERY_NAMES = " + ",".join(result)

                    else:
                        if default_section_checked and not exists:
                            exists = True

                            # add before current line
                            if i != last:
                                new_line = (
                                    "CUSTOM_BATTERY_NAMES = "
                                    + self.port
                                    + ":"
                                    + value
                                    + "\n\n"
                                    + line
                                )

                            # add at the end if last line
                            else:
                                new_line = (
                                    line
                                    + "\n\n"
                                    + "CUSTOM_BATTERY_NAMES = "
                                    + self.port
                                    + ":"
                                    + value
                                )
                        else:
                            new_line = line
                    # concatenate the new string and add an end-line break
                    config_file_new = config_file_new + new_line + "\n"

                # close the file
                file.close()
                # Open file in write mode
                write_file = open(
                    "/data/etc/dbus-serialbattery/" + utils.PATH_CONFIG_USER, "w"
                )
                # overwriting the old file contents with the new/replaced content
                write_file.write(config_file_new)
                # close the file
                write_file.close()

                # logger.error("value (saved): " + str(value))

                """
                # this removes all comments and tranfsorm the values to lowercase
                utils.config.set(
                    "DEFAULT",
                    "CUSTOM_BATTERY_NAMES",
                    self.port + ":" + value,
                )

                # Writing our configuration file to 'example.ini'
                with open(
                    "/data/etc/dbus-serialbattery/" + utils.PATH_CONFIG_USER, "w"
                ) as configfile:
                    type(utils.config.write(configfile))
                """

        except Exception:
            exception_type, exception_object, exception_traceback = sys.exc_info()
            file = exception_traceback.tb_frame.f_code.co_filename
            line = exception_traceback.tb_lineno
            logger.error(
                f"Exception occurred: {repr(exception_object)} of type {exception_type} in {file} line #{line}"
            )

        return value

    def reset_soc_callback(self, path, value):
        # callback for handling reset soc request
        return

    def force_charging_off_callback(self, path, value):
        return

    def force_discharging_off_callback(self, path, value):
        return

    def turn_balancing_off_callback(self, path, value):
        return
