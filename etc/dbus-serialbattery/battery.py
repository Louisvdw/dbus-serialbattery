# -*- coding: utf-8 -*-
from typing import Union, Tuple, List, Callable

from utils import logger
import utils
import logging
import math
from time import time
from abc import ABC, abstractmethod
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

    def __init__(self, port: str, baud: int, address: str):
        self.port: str = port
        self.baud_rate: int = baud
        self.role: str = "battery"
        self.type: str = "Generic"
        self.poll_interval: int = 1000
        self.online: bool = True
        self.hardware_version: str = None
        self.cell_count: int = None
        # max battery charge/discharge current
        self.max_battery_charge_current: float = None
        self.max_battery_discharge_current: float = None
        self.has_settings: bool = False

        # this values should only be initialized once,
        # else the BMS turns off the inverter on disconnect
        self.soc_calc_capacity_remain: float = None
        self.soc_calc_capacity_remain_lasttime: float = None
        self.soc_calc_reset_starttime: int = None
        self.soc_calc: float = None  # save soc_calc to preserve on restart
        self.soc: float = None
        self.charge_fet: bool = None
        self.discharge_fet: bool = None
        self.balance_fet: bool = None
        self.block_because_disconnect: bool = False
        self.control_charge_current: int = None
        self.control_discharge_current: int = None
        self.control_allow_charge: bool = None
        self.control_allow_discharge: bool = None

        # fetched from the BMS from a field where the user can input a custom string
        # only if available
        self.custom_field: str = None

        self.init_values()

    def init_values(self) -> None:
        """
        Used to reset values, if battery unexpectly disconnects

        :return: None
        """
        self.voltage: float = None
        self.current: float = None
        self.current_avg: float = None
        self.current_avg_lst: list = []
        self.current_corrected: float = None
        self.current_external: float = None
        self.capacity_remain: float = None
        self.capacity: float = None
        self.cycles: float = None
        self.total_ah_drawn: float = None
        self.production = None
        self.protection = Protection()
        self.version = None
        self.time_to_soc_update: int = 0
        self.temp_sensors: int = None
        self.temp1: float = None
        self.temp2: float = None
        self.temp3: float = None
        self.temp4: float = None
        self.temp_mos: float = None
        self.cells: List[Cell] = []
        self.control_voltage: float = None
        self.soc_reset_requested: bool = False
        self.soc_reset_last_reached: int = 0  # save state to preserve on restart
        self.soc_reset_battery_voltage: int = None
        self.max_battery_voltage: float = None
        self.min_battery_voltage: float = None
        self.allow_max_voltage: bool = True  # save state to preserve on restart
        self.max_voltage_start_time: int = None  # save state to preserve on restart
        self.transition_start_time: int = None
        self.charge_mode: str = None
        self.charge_mode_debug: str = ""
        self.charge_mode_debug_float: str = ""
        self.charge_mode_debug_bulk: str = ""
        self.charge_limitation: str = None
        self.discharge_limitation: str = None
        self.linear_cvl_last_set: int = 0
        self.linear_ccl_last_set: int = 0
        self.linear_dcl_last_set: int = 0
        # list of available callbacks, in order to display the buttons in the GUI
        self.available_callbacks: List[str] = []

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

        It's not possible to change the capacity or other values in some BMS
        therefore the port has to be used as unique identifier
        See https://github.com/Louisvdw/dbus-serialbattery/issues/1035

        :return: the unique identifier
        """
        if utils.USE_PORT_AS_UNIQUE_ID:
            return self.port
        else:
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
        every poll_interval milliseconds for new values true if callable should be
        used for updates as they arrive from the battery
        """
        return False

    @abstractmethod
    def refresh_data(self) -> bool:
        """
        Each driver must override this function to read battery data and populate this class
        It is called each poll just before the data is published to vedbus

        :return: false when fail, true if successful
        """
        return False

    def to_temp(self, sensor: int, value: float) -> None:
        """
        Keep the temp value between -20 and 100 to handle sensor issues or no data.
        The BMS should have already protected before those limits have been reached.

        :param sensor: temperature sensor number
        :param value: the sensor value
        :return: None
        """
        if sensor == 0:
            self.temp_mos = round(min(max(value, -20), 100), 1)
        if sensor == 1:
            self.temp1 = round(min(max(value, -20), 100), 1)
        if sensor == 2:
            self.temp2 = round(min(max(value, -20), 100), 1)
        if sensor == 3:
            self.temp3 = round(min(max(value, -20), 100), 1)
        if sensor == 4:
            self.temp4 = round(min(max(value, -20), 100), 1)

    def manage_charge_voltage(self) -> None:
        """
        Manages the charge voltage by setting `self.control_voltage`

        :return: None
        """
        if utils.SOC_CALCULATION:
            self.soc_calculation()
        else:
            self.soc_calc = self.soc

        # enable soc reset voltage management only if needed
        if utils.SOC_RESET_AFTER_DAYS is not False:
            self.soc_reset_voltage_management()

        # apply dynamic charging voltage
        if utils.CVCM_ENABLE:
            # apply linear charging voltage
            if utils.LINEAR_LIMITATION_ENABLE:
                self.manage_charge_voltage_linear()
            # apply step charging voltage
            else:
                self.manage_charge_voltage_step()
        # apply fixed charging voltage
        else:
            self.control_voltage = round(self.max_battery_voltage, 2)
            self.charge_mode = "Keep always max voltage"

    def soc_calculation(self) -> None:
        """
        Calculates the SOC based on the coulomb counting method

        :return: None
        """
        current_time = time()
        self.current_corrected = 0

        # ### only needed, if the SOC should be reset to 100% after the battery was balanced
        """
        voltage_sum = 0

        # calculate battery voltage from cell voltages
        for i in range(self.cell_count):
            voltage = self.get_cell_voltage(i)
            if voltage:
                voltage_sum += voltage
        """

        if self.soc_calc_capacity_remain is not None:
            # calculate current only, if lists are different
            if utils.SOC_CALC_CURRENT:
                # calculate current from real current
                self.current_corrected = round(
                    utils.calcLinearRelationship(
                        self.get_current(),
                        utils.SOC_CALC_CURRENT_REPORTED_BY_BMS,
                        utils.SOC_CALC_CURRENT_MEASURED_BY_USER,
                    ),
                    3,
                )
            else:
                # use current as it is
                self.current_corrected = self.get_current()

            self.soc_calc_capacity_remain = (
                self.soc_calc_capacity_remain
                + self.current_corrected
                * (current_time - self.soc_calc_capacity_remain_lasttime)
                / 3600
            )

            # limit soc_calc_capacity_remain to capacity and zero
            # in case 100% is reached and the battery is not fully charged
            # in case 0% is reached and the battery is not fully discharged
            self.soc_calc_capacity_remain = round(
                max(min(self.soc_calc_capacity_remain, self.capacity), 0), 3
            )
            self.soc_calc_capacity_remain_lasttime = current_time

            # execute checks only if one cell reaches max voltage
            # use highest cell voltage, since in this case the battery is full
            # else a unbalanced battery won't reach 100%
            if self.get_max_cell_voltage() >= utils.MAX_CELL_VOLTAGE:
                # check if battery is fully charged
                if (
                    self.get_current() < utils.SOC_RESET_CURRENT
                    and self.soc_calc_reset_starttime
                    # ### only needed, if the SOC should be reset to 100% after the battery was balanced
                    # ### in off grid situations and winter time, this will not always be the case
                    # and (self.max_battery_voltage - utils.VOLTAGE_DROP <= voltage_sum)
                ):
                    # set soc to 100%, if SOC_RESET_TIME is reached and soc_calc is not rounded 100% anymore
                    if (
                        int(current_time) - self.soc_calc_reset_starttime
                    ) > utils.SOC_RESET_TIME and round(self.soc_calc, 0) != 100:
                        logger.info("SOC set to 100%")
                        self.soc_calc_capacity_remain = self.capacity
                        self.soc_calc_reset_starttime = None
                else:
                    self.soc_calc_reset_starttime = int(current_time)

            # execute checks only if one cell reaches min voltage
            # use lowest cell voltage, since in this case the battery is empty
            # else a unbalanced battery won't reach 0% and the BMS will shut down
            if self.get_min_cell_voltage() <= utils.MIN_CELL_VOLTAGE:
                # check if battery is still being discharged
                if self.get_current() < 0 and self.soc_calc_reset_starttime:
                    # set soc to 0%, if SOC_RESET_TIME is reached and soc_calc is not rounded 0% anymore
                    if (
                        int(current_time) - self.soc_calc_reset_starttime
                    ) > utils.SOC_RESET_TIME and round(self.soc_calc, 0) != 0:
                        logger.info("SOC set to 0%")
                        self.soc_calc_capacity_remain = 0
                        self.soc_calc_reset_starttime = None
                else:
                    self.soc_calc_reset_starttime = int(current_time)
        else:
            # if soc_calc is not available initialize it from the BMS
            if self.soc_calc is None:
                # if there is a SOC from the BMS then use it
                if self.soc is not None:
                    self.soc_calc_capacity_remain = self.capacity * self.soc / 100
                    logger.info(
                        "SOC initialized from BMS and set to " + str(self.soc) + "%"
                    )
                # else set it to 100%
                # this is currently (2024.04.13) not possible, since then the driver won't start, if there is no SOC
                # but leave it in case a BMS without SOC should be added
                else:
                    self.soc_calc_capacity_remain = self.capacity
                    logger.info("SOC initialized and set to 100%")
            # else initialize it from dbus
            else:
                self.soc_calc_capacity_remain = (
                    self.capacity * self.soc_calc / 100 if self.soc > 0 else 0
                )
                logger.info(
                    "SOC initialized from dbus and set to " + str(self.soc_calc) + "%"
                )

            self.soc_calc_capacity_remain_lasttime = current_time

        # calculate the SOC based on remaining capacity
        self.soc_calc = round(
            max(min((self.soc_calc_capacity_remain / self.capacity) * 100, 100), 0), 2
        )

    def soc_reset_voltage_management(self) -> None:
        """
        Call this method only, if SOC_RESET_AFTER_DAYS is not False.

        It sets the `self.max_battery_voltage` to the `SOC_RESET_VOLTAGE` once needed.

        :return: None
        """

        soc_reset_last_reached_days_ago = (
            0
            if self.soc_reset_last_reached == 0
            else (((int(time()) - self.soc_reset_last_reached) / 60 / 60 / 24))
        )

        # set soc_reset_requested to True, if the days are over
        # it gets set to False once the bulk voltage was reached once
        if (
            utils.SOC_RESET_AFTER_DAYS is not False
            and self.soc_reset_requested is False
            and self.allow_max_voltage
            and (
                self.soc_reset_last_reached == 0
                or utils.SOC_RESET_AFTER_DAYS < soc_reset_last_reached_days_ago
            )
        ):
            self.soc_reset_requested = True

        self.soc_reset_battery_voltage = round(
            utils.SOC_RESET_VOLTAGE * self.cell_count, 2
        )

        if self.soc_reset_requested:
            self.max_battery_voltage = self.soc_reset_battery_voltage
        else:
            self.max_battery_voltage = round(
                utils.MAX_CELL_VOLTAGE * self.cell_count, 2
            )

        # TO DO: probably not needed, since it's set from the individual battery classes
        # self.min_battery_voltage = round(utils.MIN_CELL_VOLTAGE * self.cell_count, 2)

    def manage_charge_voltage_linear(self) -> None:
        """
        Manages the charge voltage using linear interpolation by setting `self.control_voltage`

        :return: None
        """
        found_high_cell_voltage = False
        voltage_sum = 0
        penalty_sum = 0
        time_diff = 0
        control_voltage = 0
        current_time = int(time())

        # meassurment and variation tolerance in volts
        measurement_tolerance_variation = 0.5

        try:
            # calculate voltage sum and check for cell overvoltage
            for i in range(self.cell_count):
                voltage = self.get_cell_voltage(i)
                if voltage:
                    voltage_sum += voltage

                    # calculate penalty sum to prevent single cell overcharge by using current cell voltage
                    if (
                        self.max_battery_voltage != self.soc_reset_battery_voltage
                        and voltage > utils.MAX_CELL_VOLTAGE
                    ):
                        # found_high_cell_voltage: reset to False is not needed, since it is recalculated every second
                        found_high_cell_voltage = True
                        penalty_sum += voltage - utils.MAX_CELL_VOLTAGE
                    elif (
                        self.max_battery_voltage == self.soc_reset_battery_voltage
                        and voltage > utils.SOC_RESET_VOLTAGE
                    ):
                        # found_high_cell_voltage: reset to False is not needed, since it is recalculated every second
                        found_high_cell_voltage = True
                        penalty_sum += voltage - utils.SOC_RESET_VOLTAGE

            voltage_cell_diff = (
                self.get_max_cell_voltage() - self.get_min_cell_voltage()
            )

            if self.max_voltage_start_time is None:
                # start timer, if max voltage is reached and cells are balanced
                if (
                    self.max_battery_voltage <= voltage_sum
                    and voltage_cell_diff
                    <= utils.CELL_VOLTAGE_DIFF_KEEP_MAX_VOLTAGE_UNTIL
                    and self.allow_max_voltage
                ):
                    self.max_voltage_start_time = current_time
                # allow max voltage again, if cells are unbalanced or SoC threshold is reached
                elif (
                    utils.SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT > self.soc_calc
                    or voltage_cell_diff
                    >= utils.CELL_VOLTAGE_DIFF_TO_RESET_VOLTAGE_LIMIT
                ) and not self.allow_max_voltage:
                    self.allow_max_voltage = True
                else:
                    pass
            else:
                if (
                    voltage_cell_diff
                    > utils.CELL_VOLTAGE_DIFF_KEEP_MAX_VOLTAGE_TIME_RESTART
                ):
                    self.max_voltage_start_time = current_time

                time_diff = current_time - self.max_voltage_start_time
                # keep max voltage for MAX_VOLTAGE_TIME_SEC more seconds
                if utils.MAX_VOLTAGE_TIME_SEC < time_diff:
                    self.allow_max_voltage = False
                    self.max_voltage_start_time = None

                    if self.soc_calc <= utils.SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT:
                        # write to log, that reset to float was not possible
                        logger.error(
                            f"Could not change to float voltage. Battery SoC ({self.soc_calc}%) is lower"
                            + f" than SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT ({utils.SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT}%)."
                            + " Please reset SoC manually or lower the SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT in the"
                            + ' "config.ini".'
                        )

                # we don't forget to reset max_voltage_start_time wenn we going to bulk(dynamic) mode
                # regardless of whether we were in absorption mode or not
                if (
                    voltage_sum
                    < self.max_battery_voltage - measurement_tolerance_variation
                ):
                    self.max_voltage_start_time = None

            # Bulk or Absorption mode
            if self.allow_max_voltage:

                # use I-Controller
                if utils.CVL_ICONTROLLER_MODE:
                    if self.control_voltage:
                        # 6 decimals are needed for a proper I-controller working
                        # https://github.com/Louisvdw/dbus-serialbattery/issues/1041
                        control_voltage = round(
                            self.control_voltage
                            - (
                                (
                                    self.get_max_cell_voltage()
                                    - (
                                        utils.SOC_RESET_VOLTAGE
                                        if self.soc_reset_requested
                                        else utils.MAX_CELL_VOLTAGE
                                    )
                                    - utils.CELL_VOLTAGE_DIFF_KEEP_MAX_VOLTAGE_UNTIL
                                )
                                * utils.CVL_ICONTROLLER_FACTOR
                            ),
                            6,
                        )
                    else:
                        control_voltage = self.max_battery_voltage

                    control_voltage = min(
                        max(control_voltage, self.min_battery_voltage),
                        self.max_battery_voltage,
                    )

                # use P-Controller
                else:
                    if found_high_cell_voltage:
                        # reduce voltage by penalty sum
                        # keep penalty above min battery voltage and below max battery voltage
                        control_voltage = round(
                            min(
                                max(
                                    voltage_sum - penalty_sum,
                                    self.min_battery_voltage,
                                ),
                                self.max_battery_voltage,
                            ),
                            6,
                        )
                    else:
                        control_voltage = self.max_battery_voltage

                self.control_voltage = control_voltage

                self.charge_mode = (
                    "Bulk" if self.max_voltage_start_time is None else "Absorption"
                )
                if found_high_cell_voltage:
                    self.charge_mode += " Dynamic"

                if self.max_battery_voltage == self.soc_reset_battery_voltage:
                    self.charge_mode += " & SoC Reset"

                if (
                    self.get_balancing()
                    and voltage_cell_diff
                    >= utils.CELL_VOLTAGE_DIFF_TO_RESET_VOLTAGE_LIMIT
                ):
                    self.charge_mode += " + Balancing"
            # Float mode
            else:
                float_voltage = round((utils.FLOAT_CELL_VOLTAGE * self.cell_count), 2)
                charge_mode = "Float"

                # reset bulk when going into float
                if self.soc_reset_requested:
                    # logger.info("set soc_reset_requested to False")
                    self.soc_reset_requested = False
                    self.soc_reset_last_reached = current_time

                if self.control_voltage:
                    # check if battery changed from bulk/absoprtion to float
                    if (
                        self.charge_mode is not None
                        and not self.charge_mode.startswith("Float")
                    ):
                        self.transition_start_time = current_time
                        self.initial_control_voltage = self.control_voltage
                        charge_mode = "Float Transition"
                        # Assume battery SOC ist 100% at this stage
                        self.trigger_soc_reset()
                    elif self.charge_mode.startswith("Float Transition"):
                        elapsed_time = current_time - self.transition_start_time
                        # Voltage reduction per second
                        VOLTAGE_REDUCTION_PER_SECOND = 0.01 / 10
                        voltage_reduction = min(
                            VOLTAGE_REDUCTION_PER_SECOND * elapsed_time,
                            self.initial_control_voltage - float_voltage,
                        )
                        self.control_voltage = (
                            self.initial_control_voltage - voltage_reduction
                        )

                        if self.control_voltage <= float_voltage:
                            self.control_voltage = float_voltage
                            charge_mode = "Float"
                        else:
                            charge_mode = "Float Transition"
                else:
                    self.control_voltage = float_voltage

                self.charge_mode = charge_mode

            self.charge_mode += " (Linear Mode)"

            # debug information
            if logger.isEnabledFor(logging.DEBUG):

                soc_reset_days_ago = round(
                    (current_time - self.soc_reset_last_reached) / 60 / 60 / 24, 2
                )
                soc_reset_in_days = round(
                    utils.SOC_RESET_AFTER_DAYS - soc_reset_days_ago, 2
                )

                self.charge_mode_debug = (
                    f"max_battery_voltage: {round(self.max_battery_voltage, 2)} V • "
                    + f"control_voltage: {round(self.control_voltage, 2)} V\n"
                    + f"voltage: {round(self.voltage, 2)} V • "
                    + f"VOLTAGE_DROP: {round(utils.VOLTAGE_DROP, 2)} V\n"
                    + f"voltage_sum: {round(voltage_sum, 2)} V • "
                    + f"voltage_cell_diff: {round(voltage_cell_diff, 3)} V\n"
                    + f"max_cell_voltage: {self.get_max_cell_voltage()} V • penalty_sum: {round(penalty_sum, 3)} V\n"
                    + f"soc: {self.soc}% • soc_calc: {self.soc_calc}%\n"
                    + f"current: {self.current}A • current_corrected: {self.current_corrected} A • "
                    + (
                        f"current_external: {self.current_external} A\n"
                        if self.current_external is not None
                        else "\n"
                    )
                    + f"current_time: {current_time}\n"
                    + f"linear_cvl_last_set: {self.linear_cvl_last_set}\n"
                    + f"charge_fet: {self.charge_fet} • control_allow_charge: {self.control_allow_charge}\n"
                    + f"discharge_fet: {self.discharge_fet} • control_allow_discharge: {self.control_allow_discharge}\n"
                    + f"block_because_disconnect: {self.block_because_disconnect}\n"
                    + "soc_reset_last_reached: "
                    + (
                        "Never"
                        if self.soc_reset_last_reached == 0
                        else f"{soc_reset_days_ago}"
                    )
                    + f" d ago, next in {soc_reset_in_days} d\n"
                    + f"soc_calc_capacity_remain: {self.soc_calc_capacity_remain}/{self.capacity} Ah\n"
                    + "soc_calc_reset_starttime: "
                    + (
                        f"{int(current_time - self.soc_calc_reset_starttime)}/{utils.SOC_RESET_TIME}"
                        if self.soc_calc_reset_starttime is not None
                        else "None"
                    )
                )

                self.charge_mode_debug_float = (
                    "-- switch to float requirements (Linear Mode) --\n"
                    + f"max_battery_voltage: {self.max_battery_voltage} <= voltage_sum: {round(voltage_sum, 2)}\n"
                    + "AND\n"
                    + f"voltage_cell_diff: {round(voltage_cell_diff, 3)} <= "
                    + "CELL_VOLTAGE_DIFF_KEEP_MAX_VOLTAGE_UNTIL: "
                    + f"{utils.CELL_VOLTAGE_DIFF_KEEP_MAX_VOLTAGE_UNTIL}\n"
                    + "AND\n"
                    + f"allow_max_voltage: {self.allow_max_voltage} == True\n"
                    + "AND\n"
                    + f"time_diff: {utils.MAX_VOLTAGE_TIME_SEC} < {time_diff}"
                )

                self.charge_mode_debug_bulk = (
                    "-- switch to bulk requirements (Linear Mode) --\n"
                    + "a) SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT: "
                    + f"{utils.SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT} > {self.soc_calc}\n"
                    + "OR\n"
                    + f"b) voltage_cell_diff: {round(voltage_cell_diff, 3)} >= "
                    + "CELL_VOLTAGE_DIFF_TO_RESET_VOLTAGE_LIMIT: "
                    + f"{utils.CELL_VOLTAGE_DIFF_TO_RESET_VOLTAGE_LIMIT}\n"
                    + "AND\n"
                    + f"allow_max_voltage: {self.allow_max_voltage} == False"
                )

        except TypeError:
            self.control_voltage = None
            self.charge_mode = "--"

    def set_cvl_linear(self, control_voltage: float) -> bool:
        """
        Set CVL only once every LINEAR_RECALCULATION_EVERY seconds or if the CVL changes more than
        LINEAR_RECALCULATION_ON_PERC_CHANGE percent

        TODO: Seems to not be needed anymore. Will be removed in future.

        :return: The status, if the CVL was set
        """
        current_time = int(time())
        diff = (
            abs(self.control_voltage - control_voltage)
            if self.control_voltage is not None
            else 0
        )

        if (
            utils.LINEAR_RECALCULATION_EVERY <= current_time - self.linear_cvl_last_set
            or (
                diff
                >= self.control_voltage
                * utils.LINEAR_RECALCULATION_ON_PERC_CHANGE
                / 100
                / 10  # for more precision, since the changes are small in this case
            )
        ):
            self.control_voltage = control_voltage
            self.linear_cvl_last_set = current_time
            return True

        return False

    def manage_charge_voltage_step(self) -> None:
        """
        Manages the charge voltage using a step function by setting `self.control_voltage`

        :return: None
        """
        voltage_sum = 0
        time_diff = 0
        current_time = int(time())

        try:
            # calculate battery sum
            for i in range(self.cell_count):
                voltage = self.get_cell_voltage(i)
                if voltage:
                    voltage_sum += voltage

            voltage_cell_diff = (
                self.get_max_cell_voltage() - self.get_min_cell_voltage()
            )

            if self.max_voltage_start_time is None:
                # check if max voltage is reached and start timer to keep max voltage
                if self.max_battery_voltage <= voltage_sum and self.allow_max_voltage:
                    # example 2
                    self.max_voltage_start_time = current_time

                # check if reset soc is greater than battery soc
                # this prevents flapping between max and float voltage
                elif (
                    utils.SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT > self.soc_calc
                    and not self.allow_max_voltage
                ):
                    self.allow_max_voltage = True

                # do nothing
                else:
                    pass

            # timer started
            else:
                time_diff = current_time - self.max_voltage_start_time
                if utils.MAX_VOLTAGE_TIME_SEC < time_diff:
                    self.allow_max_voltage = False
                    self.max_voltage_start_time = None

                else:
                    pass

            if self.allow_max_voltage:
                self.control_voltage = self.max_battery_voltage
                self.charge_mode = (
                    "Bulk" if self.max_voltage_start_time is None else "Absorption"
                )

                if self.max_battery_voltage == self.soc_reset_battery_voltage:
                    self.charge_mode += " & SoC Reset"

            else:
                # check if battery changed from bulk/absoprtion to float
                if self.charge_mode is not None and not self.charge_mode.startswith(
                    "Float"
                ):
                    # Assume battery SOC ist 100% at this stage
                    self.trigger_soc_reset()
                self.control_voltage = round(
                    utils.FLOAT_CELL_VOLTAGE * self.cell_count, 2
                )
                self.charge_mode = "Float"
                # reset bulk when going into float
                if self.soc_reset_requested:
                    # logger.info("set soc_reset_requested to False")
                    self.soc_reset_requested = False
                    self.soc_reset_last_reached = current_time

            self.charge_mode += " (Step Mode)"

            # debug information
            if logger.isEnabledFor(logging.DEBUG):

                soc_reset_days_ago = round(
                    (current_time - self.soc_reset_last_reached) / 60 / 60 / 24, 2
                )
                soc_reset_in_days = round(
                    utils.SOC_RESET_AFTER_DAYS - soc_reset_days_ago, 2
                )

                self.charge_mode_debug = (
                    f"max_battery_voltage: {round(self.max_battery_voltage, 2)} V • "
                    + f"control_voltage: {round(self.control_voltage, 2)} V\n"
                    + f"voltage: {round(self.voltage, 2)} V • "
                    + f"VOLTAGE_DROP: {round(utils.VOLTAGE_DROP, 2)} V\n"
                    + f"voltage_sum: {round(voltage_sum, 2)} V\n"
                    + f"voltage_cell_diff: {round(voltage_cell_diff, 3)} V\n"
                    + f"soc: {self.soc}% • soc_calc: {self.soc_calc}%\n"
                    + f"current: {self.current}A • current_corrected: {self.current_corrected} A • "
                    + (
                        f"current_external: {self.current_external} A\n"
                        if self.current_external is not None
                        else "\n"
                    )
                    + f"current_time: {current_time}\n"
                    + f"linear_cvl_last_set: {self.linear_cvl_last_set}\n"
                    + f"charge_fet: {self.charge_fet} • control_allow_charge: {self.control_allow_charge}\n"
                    + f"discharge_fet: {self.discharge_fet} • control_allow_discharge: {self.control_allow_discharge}\n"
                    + f"block_because_disconnect: {self.block_because_disconnect}\n"
                    + "soc_reset_last_reached: "
                    + (
                        "Never"
                        if self.soc_reset_last_reached == 0
                        else f"{soc_reset_days_ago}"
                    )
                    + f" d ago, next in {soc_reset_in_days} d\n"
                    + f"soc_calc_capacity_remain: {self.soc_calc_capacity_remain}/{self.capacity} Ah\n"
                    + "soc_calc_reset_starttime: "
                    + (
                        f"{int(current_time - self.soc_calc_reset_starttime)}/{utils.SOC_RESET_TIME}"
                        if self.soc_calc_reset_starttime is not None
                        else "None"
                    )
                )

                self.charge_mode_debug_float = (
                    "-- switch to float requirements (Step Mode) --\n"
                    + f"max_battery_voltage: {self.max_battery_voltage} <= voltage_sum: {round(voltage_sum, 2)}\n"
                    + "AND\n"
                    + f"allow_max_voltage: {self.allow_max_voltage} == True\n"
                    + "AND\n"
                    + f"time_diff: {utils.MAX_VOLTAGE_TIME_SEC} < {time_diff}"
                )

                self.charge_mode_debug_bulk = (
                    "-- switch to bulk requirements (Step Mode) --\n"
                    + "SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT: "
                    + f"{utils.SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT} > {self.soc_calc}\n"
                    + "AND\n"
                    + f"allow_max_voltage: {self.allow_max_voltage} == False"
                )

        except TypeError:
            self.control_voltage = None
            self.charge_mode = "--"

    def manage_charge_current(self) -> None:
        """
        Manages the charge current by setting `self.control_charge_current`

        :return: None
        """
        # Manage Charge Current Limitations
        charge_limits = {utils.MAX_BATTERY_CHARGE_CURRENT: "Max Battery Charge Current"}

        # if BMS limit is lower then config limit and therefore the values are not the same,
        # then the limit was also read from the BMS
        if (
            isinstance(self.max_battery_charge_current, (int, float))
            and utils.MAX_BATTERY_CHARGE_CURRENT > self.max_battery_charge_current
        ):
            charge_limits.update({self.max_battery_charge_current: "BMS Settings"})

        if utils.CCCM_CV_ENABLE:
            tmp = self.calcMaxChargeCurrentReferringToCellVoltage()
            if self.max_battery_charge_current != tmp:
                if tmp in charge_limits:
                    # do not add string, if global limitation is applied
                    if charge_limits[tmp] != "Max Battery Charge Current":
                        charge_limits.update(
                            {tmp: charge_limits[tmp] + ", Cell Voltage"}
                        )
                    else:
                        pass
                else:
                    charge_limits.update({tmp: "Cell Voltage"})

        if utils.CCCM_T_ENABLE:
            tmp = self.calcMaxChargeCurrentReferringToTemperature()
            if self.max_battery_charge_current != tmp:
                if tmp in charge_limits:
                    # do not add string, if global limitation is applied
                    if charge_limits[tmp] != "Max Battery Charge Current":
                        charge_limits.update({tmp: charge_limits[tmp] + ", Temp"})
                    else:
                        pass
                else:
                    charge_limits.update({tmp: "Temp"})

        if utils.CCCM_SOC_ENABLE:
            tmp = self.calcMaxChargeCurrentReferringToSoc()
            if self.max_battery_charge_current != tmp:
                if tmp in charge_limits:
                    # do not add string, if global limitation is applied
                    if charge_limits[tmp] != "Max Battery Charge Current":
                        charge_limits.update({tmp: charge_limits[tmp] + ", SoC"})
                    else:
                        pass
                else:
                    charge_limits.update({tmp: "SoC"})

        # set CCL to 0, if BMS does not allow to charge
        if self.charge_fet is False or self.block_because_disconnect:
            if 0 in charge_limits:
                charge_limits.update({0: charge_limits[0] + ", BMS"})
            else:
                charge_limits.update({0: "BMS"})

        """
        do not set CCL immediately, but only
        - after LINEAR_RECALCULATION_EVERY passed
        - if CCL changes to 0
        - if CCL changes more than LINEAR_RECALCULATION_ON_PERC_CHANGE
        """
        ccl = round(min(charge_limits), 3)
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

        # set allow to charge to no, if CCL is 0
        if self.control_charge_current == 0:
            self.control_allow_charge = False
        else:
            self.control_allow_charge = True

        #####

        # Manage Discharge Current Limitations
        discharge_limits = {
            utils.MAX_BATTERY_DISCHARGE_CURRENT: "Max Battery Discharge Current"
        }

        # if BMS limit is lower then config limit and therefore the values are not the same,
        # then the limit was also read from the BMS
        if (
            isinstance(self.max_battery_discharge_current, (int, float))
            and utils.MAX_BATTERY_DISCHARGE_CURRENT > self.max_battery_discharge_current
        ):
            discharge_limits.update(
                {self.max_battery_discharge_current: "BMS Settings"}
            )

        if utils.DCCM_CV_ENABLE:
            tmp = self.calcMaxDischargeCurrentReferringToCellVoltage()
            if self.max_battery_discharge_current != tmp:
                if tmp in discharge_limits:
                    # do not add string, if global limitation is applied
                    if discharge_limits[tmp] != "Max Battery Discharge Current":
                        discharge_limits.update(
                            {tmp: discharge_limits[tmp] + ", Cell Voltage"}
                        )
                    else:
                        pass
                else:
                    discharge_limits.update({tmp: "Cell Voltage"})

        if utils.DCCM_T_ENABLE:
            tmp = self.calcMaxDischargeCurrentReferringToTemperature()
            if self.max_battery_discharge_current != tmp:
                if tmp in discharge_limits:
                    # do not add string, if global limitation is applied
                    if discharge_limits[tmp] != "Max Battery Discharge Current":
                        discharge_limits.update({tmp: discharge_limits[tmp] + ", Temp"})
                    else:
                        pass
                else:
                    discharge_limits.update({tmp: "Temp"})

        if utils.DCCM_SOC_ENABLE:
            tmp = self.calcMaxDischargeCurrentReferringToSoc()
            if self.max_battery_discharge_current != tmp:
                if tmp in discharge_limits:
                    # do not add string, if global limitation is applied
                    if discharge_limits[tmp] != "Max Battery Discharge Current":
                        discharge_limits.update({tmp: discharge_limits[tmp] + ", SoC"})
                    else:
                        pass
                else:
                    discharge_limits.update({tmp: "SoC"})

        # set DCL to 0, if BMS does not allow to discharge
        if self.discharge_fet is False or self.block_because_disconnect:
            if 0 in discharge_limits:
                discharge_limits.update({0: discharge_limits[0] + ", BMS"})
            else:
                discharge_limits.update({0: "BMS"})

        """
        do not set DCL immediately, but only
        - after LINEAR_RECALCULATION_EVERY passed
        - if DCL changes to 0
        - if DCL changes more than LINEAR_RECALCULATION_ON_PERC_CHANGE
        """
        dcl = round(min(discharge_limits), 3)
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

        # set allow to discharge to no, if DCL is 0
        if self.control_discharge_current == 0:
            self.control_allow_discharge = False
        else:
            self.control_allow_discharge = True

    def calcMaxChargeCurrentReferringToCellVoltage(self) -> float:
        """
        Calculate the maximum charge current referring to the cell voltage

        :return: The maximum charge current
        """
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
            logger.warning(
                "Error while executing calcMaxChargeCurrentReferringToCellVoltage(). Using default value instead."
            )
            logger.warning(
                f"CELL_VOLTAGES_WHILE_CHARGING: {utils.CELL_VOLTAGES_WHILE_CHARGING}"
                + f" • MAX_CHARGE_CURRENT_CV: {utils.MAX_CHARGE_CURRENT_CV}"
            )

            exception_type, exception_object, exception_traceback = sys.exc_info()
            file = exception_traceback.tb_frame.f_code.co_filename
            line = exception_traceback.tb_lineno
            logger.error(
                f"Exception occurred: {repr(exception_object)} of type {exception_type} in {file} line #{line}"
            )
            return self.max_battery_charge_current

    def calcMaxDischargeCurrentReferringToCellVoltage(self) -> float:
        """
        Calculate the maximum discharge current referring to the cell voltage

        :return: The maximum discharge current
        """
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
            logger.warning(
                "Error while executing calcMaxDischargeCurrentReferringToCellVoltage(). Using default value instead."
            )
            logger.warning(
                f"CELL_VOLTAGES_WHILE_DISCHARGING: {utils.CELL_VOLTAGES_WHILE_DISCHARGING}"
                + f" • MAX_DISCHARGE_CURRENT_CV: {utils.MAX_DISCHARGE_CURRENT_CV}"
            )

            exception_type, exception_object, exception_traceback = sys.exc_info()
            file = exception_traceback.tb_frame.f_code.co_filename
            line = exception_traceback.tb_lineno
            logger.error(
                f"Exception occurred: {repr(exception_object)} of type {exception_type} in {file} line #{line}"
            )
            return self.max_battery_charge_current

    def calcMaxChargeCurrentReferringToTemperature(self) -> float:
        """
        Calculate the maximum charge current referring to the temperature

        :return: The maximum charge current
        """
        if self.get_max_temp() is None:
            return self.max_battery_charge_current

        temps = {0: self.get_max_temp(), 1: self.get_min_temp()}

        for key, currentMaxTemperature in temps.items():
            if utils.LINEAR_LIMITATION_ENABLE:
                temps[key] = utils.calcLinearRelationship(
                    currentMaxTemperature,
                    utils.TEMPERATURES_WHILE_CHARGING,
                    utils.MAX_CHARGE_CURRENT_T,
                )
            else:
                temps[key] = utils.calcStepRelationship(
                    currentMaxTemperature,
                    utils.TEMPERATURES_WHILE_CHARGING,
                    utils.MAX_CHARGE_CURRENT_T,
                    False,
                )

        return min(temps[0], temps[1])

    def calcMaxDischargeCurrentReferringToTemperature(self) -> float:
        """
        Calculate the maximum discharge current referring to the temperature

        :return: The maximum discharge current
        """
        if self.get_max_temp() is None:
            return self.max_battery_discharge_current

        temps = {0: self.get_max_temp(), 1: self.get_min_temp()}

        for key, currentMaxTemperature in temps.items():
            if utils.LINEAR_LIMITATION_ENABLE:
                temps[key] = utils.calcLinearRelationship(
                    currentMaxTemperature,
                    utils.TEMPERATURES_WHILE_DISCHARGING,
                    utils.MAX_DISCHARGE_CURRENT_T,
                )
            else:
                temps[key] = utils.calcStepRelationship(
                    currentMaxTemperature,
                    utils.TEMPERATURES_WHILE_DISCHARGING,
                    utils.MAX_DISCHARGE_CURRENT_T,
                    True,
                )

        return min(temps[0], temps[1])

    def calcMaxChargeCurrentReferringToSoc(self) -> float:
        """
        Calculate the maximum charge current referring to the SoC

        :return: The maximum charge current
        """
        try:
            if utils.LINEAR_LIMITATION_ENABLE:
                return utils.calcLinearRelationship(
                    self.soc_calc,
                    utils.SOC_WHILE_CHARGING,
                    utils.MAX_CHARGE_CURRENT_SOC,
                )
            return utils.calcStepRelationship(
                self.soc_calc,
                utils.SOC_WHILE_CHARGING,
                utils.MAX_CHARGE_CURRENT_SOC,
                True,
            )
        except Exception:
            logger.warning(
                "Error while executing calcMaxChargeCurrentReferringToSoc(). Using default value instead."
            )
            logger.warning(
                f"SOC_WHILE_CHARGING: {utils.SOC_WHILE_CHARGING}"
                + f" • MAX_CHARGE_CURRENT_SOC: {utils.MAX_CHARGE_CURRENT_SOC}"
            )

            exception_type, exception_object, exception_traceback = sys.exc_info()
            file = exception_traceback.tb_frame.f_code.co_filename
            line = exception_traceback.tb_lineno
            logger.error(
                f"Exception occurred: {repr(exception_object)} of type {exception_type} in {file} line #{line}"
            )
            return self.max_battery_charge_current

    def calcMaxDischargeCurrentReferringToSoc(self) -> float:
        """
        Calculate the maximum discharge current referring to the SoC

        :return: The maximum discharge current
        """
        try:
            if utils.LINEAR_LIMITATION_ENABLE:
                return utils.calcLinearRelationship(
                    self.soc_calc,
                    utils.SOC_WHILE_DISCHARGING,
                    utils.MAX_DISCHARGE_CURRENT_SOC,
                )
            return utils.calcStepRelationship(
                self.soc_calc,
                utils.SOC_WHILE_DISCHARGING,
                utils.MAX_DISCHARGE_CURRENT_SOC,
                True,
            )
        except Exception:
            logger.warning(
                "Error while executing calcMaxDischargeCurrentReferringToSoc(). Using default value instead."
            )
            logger.warning(
                f"SOC_WHILE_DISCHARGING: {utils.SOC_WHILE_DISCHARGING}"
                + f" • MAX_DISCHARGE_CURRENT_SOC: {utils.MAX_DISCHARGE_CURRENT_SOC}"
            )

            exception_type, exception_object, exception_traceback = sys.exc_info()
            file = exception_traceback.tb_frame.f_code.co_filename
            line = exception_traceback.tb_lineno
            logger.error(
                f"Exception occurred: {repr(exception_object)} of type {exception_type} in {file} line #{line}"
            )
            return self.max_battery_discharge_current

    def get_min_cell(self) -> int:
        """
        Get the cell with the lowest voltage

        :return: The number of the cell with the lowest voltage
        """
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
        """
        Get the cell with the highest voltage

        :return: The number of the cell with the highest voltage
        """
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
        """
        Get the description of the cell with the lowest voltage

        :return: The description of the cell with the lowest voltage
        """
        cell_no = self.get_min_cell()
        return cell_no if cell_no is None else "C" + str(cell_no + 1)

    def get_max_cell_desc(self) -> Union[str, None]:
        """
        Get the description of the cell with the highest voltage

        :return: The description of the cell with the highest voltage
        """
        cell_no = self.get_max_cell()
        return cell_no if cell_no is None else "C" + str(cell_no + 1)

    def get_cell_voltage(self, idx: int) -> Union[float, None]:
        """
        Get the voltage of a specific cell

        :param idx: The index of the cell
        :return: The voltage of the cell
        """
        if idx >= min(len(self.cells), self.cell_count):
            return None
        return self.cells[idx].voltage

    def get_cell_voltage_sum(self) -> float:
        """
        This method returns the sum of all cell voltages

        :return: The sum of all cell voltages
        """
        voltage_sum = 0
        for i in range(self.cell_count):
            voltage = self.get_cell_voltage(i)
            if voltage:
                voltage_sum += voltage
        return voltage_sum

    def get_cell_balancing(self, idx: int) -> Union[int, None]:
        if idx >= min(len(self.cells), self.cell_count):
            return None
        if self.cells[idx].balance is not None and self.cells[idx].balance:
            return 1
        return 0

    def get_capacity_remain(self) -> Union[float, None]:
        if self.capacity_remain is not None:
            return self.capacity_remain
        if self.capacity is not None and self.soc_calc is not None:
            return self.capacity * self.soc_calc / 100
        return None

    def get_timeToSoc(
        self, soc_target: float, percent_per_second: float, only_number: bool = False
    ) -> str:
        if self.get_current() > 0:
            soc_diff = soc_target - self.soc_calc
        else:
            soc_diff = self.soc_calc - soc_target

        """
        calculate only positive SoC points, since negative points have no sense
        when charging only points above current SoC are shown
        when discharging only points below current SoC are shown
        """
        if soc_diff < 0:
            return None

        time_to_go_str = None
        if (
            self.soc_calc != soc_target
            and percent_per_second != 0
            and (soc_diff > 0 or utils.TIME_TO_SOC_INC_FROM is True)
        ):
            seconds_to_go = int(soc_diff / percent_per_second)
            time_to_go_str = ""

            if only_number or utils.TIME_TO_SOC_VALUE_TYPE & 1:
                time_to_go_str += str(seconds_to_go)
                if not only_number and utils.TIME_TO_SOC_VALUE_TYPE & 2:
                    time_to_go_str += " ["
            if not only_number and utils.TIME_TO_SOC_VALUE_TYPE & 2:
                time_to_go_str += self.get_secondsToString(seconds_to_go)

                if utils.TIME_TO_SOC_VALUE_TYPE & 1:
                    time_to_go_str += "]"

        return time_to_go_str

    def get_secondsToString(self, timespan: int, precision: int = 3) -> str:
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

    def get_allow_to_charge(self) -> bool:
        return (
            True
            if self.charge_fet
            and self.control_allow_charge
            and self.block_because_disconnect is False
            else False
        )

    def get_allow_to_discharge(self) -> bool:
        return (
            True
            if self.discharge_fet
            and self.control_allow_discharge
            and self.block_because_disconnect is False
            else False
        )

    def get_allow_to_balance(self) -> bool:
        return True if self.balance_fet else False

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

    def monitor_external_current(self) -> None:
        """
        Start monitoring the external current sensor
        """
        from dbusmonitor import DbusMonitor

        logger.info(
            "Monitoring external current using: "
            + f"{utils.EXTERNAL_CURRENT_SENSOR_DBUS_DEVICE}{utils.EXTERNAL_CURRENT_SENSOR_DBUS_PATH}"
        )

        # ### read values from battery
        # Why this dummy? Because DbusMonitor expects these values to be there, even though we don't
        # need them. So just add some dummy data. This can go away when DbusMonitor is more generic.
        dummy = {"code": None, "whenToLog": "configChange", "accessLevel": None}

        # remove device name from dbus service name
        device_splitted = utils.EXTERNAL_CURRENT_SENSOR_DBUS_DEVICE.split(".")
        dbus_service = ".".join(device_splitted[:3])

        dbus_tree = {
            dbus_service: {
                utils.EXTERNAL_CURRENT_SENSOR_DBUS_PATH: dummy,
            }
        }

        # start monitoring
        self._dbusmonitor = DbusMonitor(
            dbus_tree, valueChangedCallback=self._dbus_value_changed
        )

    def _dbus_value_changed(
        self, dbusServiceName, dbusPath, dict, changes, deviceInstance
    ):
        if (
            dbusServiceName == utils.EXTERNAL_CURRENT_SENSOR_DBUS_DEVICE
            and dbusPath == utils.EXTERNAL_CURRENT_SENSOR_DBUS_PATH
        ):
            self.current_external = round(changes["Value"], 2)
            logger.debug(
                f"dbusServiceName: {dbusServiceName} - dbusPath: {dbusPath} - value: {changes['Value']}"
            )

    def get_current(self) -> Union[float, None]:
        """
        Get the current from the battery.
        If an external current sensor is connected, use that value.
        """
        if self.current_external is not None:
            return self.current_external
        return self.current

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
            f"> Connection voltage: {self.voltage} V | Current: {self.get_current()} A | SoC: {self.soc_calc}%"
        )
        logger.info(
            f"> Cell count: {self.cell_count} | Cells populated: {cell_counter}"
        )
        logger.info(f"> LINEAR LIMITATION ENABLE: {utils.LINEAR_LIMITATION_ENABLE}")
        logger.info(
            f"> MIN CELL VOLTAGE: {utils.MIN_CELL_VOLTAGE} V | MAX CELL VOLTAGE: {utils.MAX_CELL_VOLTAGE} V"
        )
        logger.info(
            f"> MAX BATTERY CHARGE CURRENT: {utils.MAX_BATTERY_CHARGE_CURRENT} A | "
            + f"MAX BATTERY DISCHARGE CURRENT: {utils.MAX_BATTERY_DISCHARGE_CURRENT} A"
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
                f"> MAX BATTERY CHARGE CURRENT: {self.max_battery_charge_current} A | "
                + f"MAX BATTERY DISCHARGE CURRENT: {self.max_battery_discharge_current} A (read from BMS)"
            )
        logger.info(f"> CVCM:     {utils.CVCM_ENABLE}")
        logger.info(
            f"> CCCM CV:  {str(utils.CCCM_CV_ENABLE).ljust(5)} | DCCM CV:  {utils.DCCM_CV_ENABLE}"
        )
        logger.info(
            f"> CCCM T:   {str(utils.CCCM_T_ENABLE).ljust(5)} | DCCM T:   {utils.DCCM_T_ENABLE}"
        )
        logger.info(
            f"> CCCM SOC: {str(utils.CCCM_SOC_ENABLE).ljust(5)} | DCCM SOC: {utils.DCCM_SOC_ENABLE}"
        )
        logger.info(
            f"> CHARGE FET: {self.charge_fet} | DISCHARGE FET: {self.discharge_fet} | BALANCE FET: {self.balance_fet}"
        )
        logger.info(f"Serial Number/Unique Identifier: {self.unique_identifier()}")

        return

    def reset_soc_callback(self, path: str, value: int) -> bool:
        # callback for handling reset soc request
        return False  # return False to indicate that the callback was not handled

    def force_charging_off_callback(self, path: str, value: int) -> bool:
        return False  # return False to indicate that the callback was not handled

    def force_discharging_off_callback(self, path: str, value: int) -> bool:
        return False  # return False to indicate that the callback was not handled

    def turn_balancing_off_callback(self, path: str, value: int) -> bool:
        return False  # return False to indicate that the callback was not handled

    def trigger_soc_reset(self) -> bool:
        """
        This method can be used to implement SOC reset when the battery is assumed to be full
        """
        return False  # return False to indicate that the callback was not handled
