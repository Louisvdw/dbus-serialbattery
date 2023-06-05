# -*- coding: utf-8 -*-
import logging

import configparser
from pathlib import Path
from typing import List, Any, Callable

import serial
from time import sleep
from struct import unpack_from
import bisect

# Logging
logging.basicConfig()
logger = logging.getLogger("SerialBattery")
logger.setLevel(logging.INFO)

config = configparser.ConfigParser()
path = Path(__file__).parents[0]
default_config_file_path = path.joinpath("config.default.ini").absolute().__str__()
custom_config_file_path = path.joinpath("config.ini").absolute().__str__()
config.read([default_config_file_path, custom_config_file_path])


def _get_list_from_config(
    group: str, option: str, mapper: Callable[[Any], Any] = lambda v: v
) -> List[Any]:
    rawList = config[group][option].split(",")
    return list(
        map(
            mapper,
            [item.strip() for item in rawList if item != "" and item is not None],
        )
    )


# battery types
# if not specified: baud = 9600

# Constants - Need to dynamically get them in future
DRIVER_VERSION = "1.0.20230526dev"
zero_char = chr(48)
degree_sign = "\N{DEGREE SIGN}"

# --------- Battery Current limits ---------
MAX_BATTERY_CHARGE_CURRENT = float(config["DEFAULT"]["MAX_BATTERY_CHARGE_CURRENT"])
MAX_BATTERY_DISCHARGE_CURRENT = float(
    config["DEFAULT"]["MAX_BATTERY_DISCHARGE_CURRENT"]
)

# --------- Cell Voltages ---------
# Description: Cell min/max voltages which are used to calculate the min/max battery voltage
# Example: 16 cells * 3.45V/cell = 55.2V max charge voltage. 16 cells * 2.90V = 46.4V min discharge voltage
MIN_CELL_VOLTAGE = float(config["DEFAULT"]["MIN_CELL_VOLTAGE"])
MAX_CELL_VOLTAGE = float(config["DEFAULT"]["MAX_CELL_VOLTAGE"])
# Max voltage can seen as absorption voltage
FLOAT_CELL_VOLTAGE = float(config["DEFAULT"]["FLOAT_CELL_VOLTAGE"])

# --------- BMS disconnect behaviour ---------
# Description: Block charge and discharge when the communication to the BMS is lost. If you are removing the
#              BMS on purpose, then you have to restart the driver/system to reset the block.
# False: Charge and discharge is not blocked on BMS communication loss
# True: Charge and discharge is blocked on BMS communication loss, it's unblocked when connection is established
#       again or the driver/system is restarted
BLOCK_ON_DISCONNECT = "True" == config["DEFAULT"]["BLOCK_ON_DISCONNECT"]

# --------- Charge mode ---------
# Choose the mode for voltage / current limitations (True / False)
# False is a step mode: This is the default with limitations on hard boundary steps
# True is a linear mode:
#     For CCL and DCL the values between the steps are calculated for smoother values (by WaldemarFech)
#     For CVL max battery voltage is calculated dynamically in order that the max cell voltage is not exceeded
LINEAR_LIMITATION_ENABLE = "True" == config["DEFAULT"]["LINEAR_LIMITATION_ENABLE"]

# Specify in seconds how often the penalty should be recalculated
LINEAR_RECALCULATION_EVERY = int(config["DEFAULT"]["LINEAR_RECALCULATION_EVERY"])
# Specify in percent when the linear values should be recalculated immediately
# Example: 5 for a immediate change, when the value changes by more than 5%
LINEAR_RECALCULATION_ON_PERC_CHANGE = int(
    config["DEFAULT"]["LINEAR_RECALCULATION_ON_PERC_CHANGE"]
)


# --------- Charge Voltage limitation (affecting CVL) ---------
# Description: Limit max charging voltage (MAX_CELL_VOLTAGE * cell count), switch from max voltage to float
#              voltage (FLOAT_CELL_VOLTAGE * cell count) and back
#     False: Max charging voltage is always kept
#     True: Max charging voltage is reduced based on charge mode
#         Step mode: After max voltage is reached for MAX_VOLTAGE_TIME_SEC it switches to float voltage. After
#                    SoC is below SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT it switches back to max voltage.
#         Linear mode: After max voltage is reachend and cell voltage difference is smaller or equal to
#                      CELL_VOLTAGE_DIFF_KEEP_MAX_VOLTAGE_UNTIL it switches to float voltage after 300 (fixed)
#                      additional seconds.
#                      After cell voltage difference is greater or equal to CELL_VOLTAGE_DIFF_TO_RESET_VOLTAGE_LIMIT
#                      OR
#                      SoC is below SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT
#                      it switches back to max voltage.
# Example: The battery reached max voltage of 55.2V and hold it for 900 seconds, the the CVL is switched to
#          float voltage of 53.6V to don't stress the batteries. Allow max voltage of 55.2V again, if SoC is
#          once below 90%
#          OR
#          The battery reached max voltage of 55.2V and the max cell difference is 0.010V, then switch to float
#          voltage of 53.6V after 300 additional seconds to don't stress the batteries. Allow max voltage of
#          55.2V again if max cell difference is above 0.080V or SoC below 90%.
# Charge voltage control management enable (True/False).
CVCM_ENABLE = "True" == config["DEFAULT"]["CVCM_ENABLE"]

# -- CVL reset based on cell voltage diff (linear mode)
# Specify cell voltage diff where CVL limit is kept until diff is equal or lower
CELL_VOLTAGE_DIFF_KEEP_MAX_VOLTAGE_UNTIL = float(
    config["DEFAULT"]["CELL_VOLTAGE_DIFF_KEEP_MAX_VOLTAGE_UNTIL"]
)
# Specify cell voltage diff where CVL limit is reset to max voltage, if value get above
# the cells are considered as imbalanced, if the cell diff exceeds 5% of the nominal cell voltage
# e.g. 3.2 V * 5 / 100 = 0.160 V
CELL_VOLTAGE_DIFF_TO_RESET_VOLTAGE_LIMIT = float(
    config["DEFAULT"]["CELL_VOLTAGE_DIFF_TO_RESET_VOLTAGE_LIMIT"]
)

# -- CVL Reset based on SoC option
# Specify how long the max voltage should be kept, if reached then switch to float voltage
MAX_VOLTAGE_TIME_SEC = float(config["DEFAULT"]["MAX_VOLTAGE_TIME_SEC"])
# Specify SoC where CVL limit is reset to max voltage, if value gets below
SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT = float(
    config["DEFAULT"]["SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT"]
)


# --------- Cell Voltage Current limitation (affecting CCL/DCL) ---------
# Description: Maximal charge / discharge current will be in-/decreased depending on min and max cell voltages
# Example: 18 cells * 3.55V/cell = 63.9V max charge voltage
#          18 cells * 2.70V/cell = 48.6V min discharge voltage
#          But in reality not all cells reach the same voltage at the same time. The (dis)charge current
#          will be (in-/)decreased, if even ONE SINGLE BATTERY CELL reaches the limits

# Charge current control management referring to cell-voltage enable (True/False).
CCCM_CV_ENABLE = "True" == config["DEFAULT"]["CCCM_CV_ENABLE"]
# Discharge current control management referring to cell-voltage enable (True/False).
DCCM_CV_ENABLE = "True" == config["DEFAULT"]["DCCM_CV_ENABLE"]

# Set steps to reduce battery current
# The current will be changed linear between those steps if LINEAR_LIMITATION_ENABLE is set to True
CELL_VOLTAGES_WHILE_CHARGING = _get_list_from_config(
    "DEFAULT", "CELL_VOLTAGES_WHILE_CHARGING", lambda v: float(v)
)
MAX_CHARGE_CURRENT_CV = _get_list_from_config(
    "DEFAULT",
    "MAX_CHARGE_CURRENT_CV_FRACTION",
    lambda v: MAX_BATTERY_CHARGE_CURRENT * float(v),
)

CELL_VOLTAGES_WHILE_DISCHARGING = _get_list_from_config(
    "DEFAULT", "CELL_VOLTAGES_WHILE_DISCHARGING", lambda v: float(v)
)
MAX_DISCHARGE_CURRENT_CV = _get_list_from_config(
    "DEFAULT",
    "MAX_DISCHARGE_CURRENT_CV_FRACTION",
    lambda v: MAX_BATTERY_DISCHARGE_CURRENT * float(v),
)


# --------- Temperature limitation (affecting CCL/DCL) ---------
# Description: Maximal charge / discharge current will be in-/decreased depending on temperature
# Example: The temperature limit will be monitored to control the currents. If there are two temperature senors,
#          then the worst case will be calculated and the more secure lower current will be set.
# Charge current control management referring to temperature enable (True/False).
CCCM_T_ENABLE = "True" == config["DEFAULT"]["CCCM_T_ENABLE"]
# Charge current control management referring to temperature enable (True/False).
DCCM_T_ENABLE = "True" == config["DEFAULT"]["DCCM_T_ENABLE"]

# Set steps to reduce battery current
# The current will be changed linear between those steps if LINEAR_LIMITATION_ENABLE is set to True
TEMPERATURE_LIMITS_WHILE_CHARGING = _get_list_from_config(
    "DEFAULT", "TEMPERATURE_LIMITS_WHILE_CHARGING", lambda v: float(v)
)
MAX_CHARGE_CURRENT_T = _get_list_from_config(
    "DEFAULT",
    "MAX_CHARGE_CURRENT_T_FRACTION",
    lambda v: MAX_BATTERY_CHARGE_CURRENT * float(v),
)

TEMPERATURE_LIMITS_WHILE_DISCHARGING = _get_list_from_config(
    "DEFAULT", "TEMPERATURE_LIMITS_WHILE_DISCHARGING", lambda v: float(v)
)
MAX_DISCHARGE_CURRENT_T = _get_list_from_config(
    "DEFAULT",
    "MAX_DISCHARGE_CURRENT_T_FRACTION",
    lambda v: MAX_BATTERY_DISCHARGE_CURRENT * float(v),
)


# --------- SOC limitation (affecting CCL/DCL) ---------
# Description: Maximal charge / discharge current will be increased / decreased depending on State of Charge,
#              see CC_SOC_LIMIT1 etc.
# Example: The SoC limit will be monitored to control the currents.
# Charge current control management enable (True/False).
CCCM_SOC_ENABLE = "True" == config["DEFAULT"]["CCCM_SOC_ENABLE"]
# Discharge current control management enable (True/False).
DCCM_SOC_ENABLE = "True" == config["DEFAULT"]["DCCM_SOC_ENABLE"]

# Charge current soc limits
CC_SOC_LIMIT1 = float(config["DEFAULT"]["CC_SOC_LIMIT1"])
CC_SOC_LIMIT2 = float(config["DEFAULT"]["CC_SOC_LIMIT2"])
CC_SOC_LIMIT3 = float(config["DEFAULT"]["CC_SOC_LIMIT3"])

# Charge current limits
CC_CURRENT_LIMIT1 = MAX_BATTERY_CHARGE_CURRENT * float(
    config["DEFAULT"]["CC_CURRENT_LIMIT1_FRACTION"]
)
CC_CURRENT_LIMIT2 = MAX_BATTERY_CHARGE_CURRENT * float(
    config["DEFAULT"]["CC_CURRENT_LIMIT2_FRACTION"]
)
CC_CURRENT_LIMIT3 = MAX_BATTERY_CHARGE_CURRENT * float(
    config["DEFAULT"]["CC_CURRENT_LIMIT3_FRACTION"]
)

# Discharge current soc limits
DC_SOC_LIMIT1 = float(config["DEFAULT"]["DC_SOC_LIMIT1"])
DC_SOC_LIMIT2 = float(config["DEFAULT"]["DC_SOC_LIMIT2"])
DC_SOC_LIMIT3 = float(config["DEFAULT"]["DC_SOC_LIMIT3"])

# Discharge current limits
DC_CURRENT_LIMIT1 = MAX_BATTERY_DISCHARGE_CURRENT * float(
    config["DEFAULT"]["DC_CURRENT_LIMIT1_FRACTION"]
)
DC_CURRENT_LIMIT2 = MAX_BATTERY_DISCHARGE_CURRENT * float(
    config["DEFAULT"]["DC_CURRENT_LIMIT2_FRACTION"]
)
DC_CURRENT_LIMIT3 = MAX_BATTERY_DISCHARGE_CURRENT * float(
    config["DEFAULT"]["DC_CURRENT_LIMIT3_FRACTION"]
)


# --------- Time-To-Go ---------
# Description: Calculates the time to go shown in the GUI
TIME_TO_GO_ENABLE = "True" == config["DEFAULT"]["TIME_TO_GO_ENABLE"]

# --------- Time-To-Soc ---------
# Description: Calculates the time to a specific SoC
# Example: TIME_TO_SOC_POINTS = 50, 25, 15, 0
#          6h 24m remaining until 50% SoC
#          17h 36m remaining until 25% SoC
#          22h 5m remaining until 15% SoC
#          28h 48m remaining until 0% SoC
# Set of SoC percentages to report on dbus and MQTT. The more you specify the more it will impact system performance.
# [Valid values 0-100, comma separated list. More that 20 intervals are not recommended]
# Example: TIME_TO_SOC_POINTS = 100, 95, 90, 85, 75, 50, 25, 20, 10, 0
# Leave empty to disable
TIME_TO_SOC_POINTS = _get_list_from_config(
    "DEFAULT", "TIME_TO_SOC_POINTS", lambda v: int(v)
)
# Specify TimeToSoc value type [Valid values 1, 2, 3]
# 1 Seconds
# 2 Time string <days>d <hours>h <minutes>m <seconds>s
# 3 Both seconds and time string "<seconds> [<days>d <hours>h <minutes>m <seconds>s]"
TIME_TO_SOC_VALUE_TYPE = int(config["DEFAULT"]["TIME_TO_SOC_VALUE_TYPE"])
# Specify in seconds how often the TimeToSoc should be recalculated
# Minimum are 5 seconds to prevent CPU overload
TIME_TO_SOC_RECALCULATE_EVERY = (
    int(config["DEFAULT"]["TIME_TO_SOC_RECALCULATE_EVERY"])
    if int(config["DEFAULT"]["TIME_TO_SOC_RECALCULATE_EVERY"]) > 5
    else 5
)
# Include TimeToSoC points when moving away from the SoC point [Valid values True, False]
# These will be as negative time. Disabling this improves performance slightly
TIME_TO_SOC_INC_FROM = "True" == config["DEFAULT"]["TIME_TO_SOC_INC_FROM"]


# --------- Additional settings ---------
# Specify only one BMS type to load else leave empty to try to load all available
# -- Available BMS:
# Daly, Ecs, HeltecModbus, HLPdataBMS4S, Jkbms, Lifepower, LltJbd, Renogy, Seplos
# -- Available BMS, but disabled by default:
# https://louisvdw.github.io/dbus-serialbattery/general/install#how-to-enable-a-disabled-bms
# Ant, MNB, Sinowealth
BMS_TYPE = config["DEFAULT"]["BMS_TYPE"]

EXCLUDED_DEVICES = _get_list_from_config(
    "DEFAULT", "EXCLUDED_DEVICES", lambda v: str(v)
)

# Publish the config settings to the dbus path "/Info/Config/"
PUBLISH_CONFIG_VALUES = int(config["DEFAULT"]["PUBLISH_CONFIG_VALUES"])

# Select the format of cell data presented on dbus [Valid values 0,1,2,3]
# 0 Do not publish all the cells (only the min/max cell data as used by the default GX)
# 1 Format: /Voltages/Cell (also available for display on Remote Console)
# 2 Format: /Cell/#/Volts
# 3 Both formats 1 and 2
BATTERY_CELL_DATA_FORMAT = int(config["DEFAULT"]["BATTERY_CELL_DATA_FORMAT"])

# Simulate Midpoint graph (True/False).
MIDPOINT_ENABLE = "True" == config["DEFAULT"]["MIDPOINT_ENABLE"]

# Battery temperature
# Specifiy how the battery temperature is assembled
# 0 Get mean of temp sensor 1 and temp sensor 2
# 1 Get only temp from temp sensor 1
# 2 Get only temp from temp sensor 2
TEMP_BATTERY = int(config["DEFAULT"]["TEMP_BATTERY"])

# Temperature sensor 1 name
TEMP_1_NAME = config["DEFAULT"]["TEMP_1_NAME"]

# Temperature sensor 2 name
TEMP_2_NAME = config["DEFAULT"]["TEMP_2_NAME"]

# Temperature sensor 3 name
TEMP_3_NAME = config["DEFAULT"]["TEMP_3_NAME"]

# Temperature sensor 2 name
TEMP_4_NAME = config["DEFAULT"]["TEMP_4_NAME"]


# --------- BMS specific settings ---------

# -- LltJbd settings
# SoC low levels
# NOTE: SOC_LOW_WARNING is also used to calculate the Time-To-Go even if you are not using a LltJbd BMS
SOC_LOW_WARNING = float(config["DEFAULT"]["SOC_LOW_WARNING"])
SOC_LOW_ALARM = float(config["DEFAULT"]["SOC_LOW_ALARM"])

# -- Daly settings
# Battery capacity (amps) if the BMS does not support reading it
BATTERY_CAPACITY = float(config["DEFAULT"]["BATTERY_CAPACITY"])
# Invert Battery Current. Default non-inverted. Set to -1 to invert
INVERT_CURRENT_MEASUREMENT = int(config["DEFAULT"]["INVERT_CURRENT_MEASUREMENT"])

# -- ESC GreenMeter and Lipro device settings
GREENMETER_ADDRESS = int(config["DEFAULT"]["GREENMETER_ADDRESS"])
LIPRO_START_ADDRESS = int(config["DEFAULT"]["LIPRO_START_ADDRESS"])
LIPRO_END_ADDRESS = int(config["DEFAULT"]["LIPRO_END_ADDRESS"])
LIPRO_CELL_COUNT = int(config["DEFAULT"]["LIPRO_CELL_COUNT"])

# -- HeltecModbus device settings
HELTEC_MODBUS_ADDR = _get_list_from_config(
    "DEFAULT", "HELTEC_MODBUS_ADDR", lambda v: int(v)
)


# --------- Battery monitor specific settings ---------
# If you are using a SmartShunt or something else as a battery monitor, the battery voltage reported
# from the BMS and SmartShunt could differ. This causes, that the driver never goapplies the float voltage,
# since max voltage is never reached.
# Example:
#     cell count: 16
#     MAX_CELL_VOLTAGE = 3.45
#     max voltage calculated = 16 * 3.45 = 55.20
#     CVL is set to 55.20 and the battery is now charged until the SmartShunt measures 55.20 V. The BMS
#     now measures 55.05 V since there is a voltage drop of 0.15 V. Since the dbus-serialbattery measures
#     55.05 V the max voltage is never reached for the driver and max voltage is kept forever.
#     Set VOLTAGE_DROP to 0.15
VOLTAGE_DROP = float(config["DEFAULT"]["VOLTAGE_DROP"])


# --------- Functions ---------
def constrain(val, min_val, max_val):
    if min_val > max_val:
        min_val, max_val = max_val, min_val
    return min(max_val, max(min_val, val))


def mapRange(inValue, inMin, inMax, outMin, outMax):
    return outMin + (((inValue - inMin) / (inMax - inMin)) * (outMax - outMin))


def mapRangeConstrain(inValue, inMin, inMax, outMin, outMax):
    return constrain(mapRange(inValue, inMin, inMax, outMin, outMax), outMin, outMax)


def calcLinearRelationship(inValue, inArray, outArray):
    if inArray[0] > inArray[-1]:  # change compare-direction in array
        return calcLinearRelationship(inValue, inArray[::-1], outArray[::-1])
    else:
        # Handle out of bounds
        if inValue <= inArray[0]:
            return outArray[0]
        if inValue >= inArray[-1]:
            return outArray[-1]

        # else calculate linear current between the setpoints
        idx = bisect.bisect(inArray, inValue)
        upperIN = inArray[idx - 1]  # begin with idx 0 as max value
        upperOUT = outArray[idx - 1]
        lowerIN = inArray[idx]
        lowerOUT = outArray[idx]
        return mapRangeConstrain(inValue, lowerIN, upperIN, lowerOUT, upperOUT)


def calcStepRelationship(inValue, inArray, outArray, returnLower):
    if inArray[0] > inArray[-1]:  # change compare-direction in array
        return calcStepRelationship(inValue, inArray[::-1], outArray[::-1], returnLower)

    # Handle out of bounds
    if inValue <= inArray[0]:
        return outArray[0]
    if inValue >= inArray[-1]:
        return outArray[-1]

    # else get index between the setpoints
    idx = bisect.bisect(inArray, inValue)

    return outArray[idx] if returnLower else outArray[idx - 1]


def is_bit_set(tmp):
    return False if tmp == zero_char else True


def kelvin_to_celsius(kelvin_temp):
    return kelvin_temp - 273.1


def format_value(value, prefix, suffix):
    return (
        None
        if value is None
        else ("" if prefix is None else prefix)
        + str(value)
        + ("" if suffix is None else suffix)
    )


def read_serial_data(
    command, port, baud, length_pos, length_check, length_fixed=None, length_size=None
):
    try:
        with serial.Serial(port, baudrate=baud, timeout=0.1) as ser:
            return read_serialport_data(
                ser, command, length_pos, length_check, length_fixed, length_size
            )

    except serial.SerialException as e:
        logger.error(e)
        return False


# Open the serial port
# Return variable for the openned port
def open_serial_port(port, baud):
    ser = None
    tries = 3
    while tries > 0:
        try:
            ser = serial.Serial(port, baudrate=baud, timeout=0.1)
            tries = 0
        except serial.SerialException as e:
            logger.error(e)
            tries -= 1

    return ser


# Read data from previously opened serial port
def read_serialport_data(
    ser: serial.Serial,
    command,
    length_pos,
    length_check,
    length_fixed=None,
    length_size=None,
):
    try:
        ser.flushOutput()
        ser.flushInput()
        ser.write(command)

        length_byte_size = 1
        if length_size is not None:
            if length_size.upper() == "H":
                length_byte_size = 2
            elif length_size.upper() == "I" or length_size.upper() == "L":
                length_byte_size = 4

        count = 0
        toread = ser.inWaiting()

        while toread < (length_pos + length_byte_size):
            sleep(0.005)
            toread = ser.inWaiting()
            count += 1
            if count > 50:
                logger.error(">>> ERROR: No reply - returning")
                return False

        # logger.info('serial data toread ' + str(toread))
        res = ser.read(toread)
        if length_fixed is not None:
            length = length_fixed
        else:
            if len(res) < (length_pos + length_byte_size):
                logger.error(
                    ">>> ERROR: No reply - returning [len:" + str(len(res)) + "]"
                )
                return False
            length_size = length_size if length_size is not None else "B"
            length = unpack_from(">" + length_size, res, length_pos)[0]

        # logger.info('serial data length ' + str(length))

        count = 0
        data = bytearray(res)
        while len(data) <= length + length_check:
            res = ser.read(length + length_check)
            data.extend(res)
            # logger.info('serial data length ' + str(len(data)))
            sleep(0.005)
            count += 1
            if count > 150:
                logger.error(
                    ">>> ERROR: No reply - returning [len:"
                    + str(len(data))
                    + "/"
                    + str(length + length_check)
                    + "]"
                )
                return False

        return data

    except serial.SerialException as e:
        logger.error(e)
        return False


locals_copy = locals().copy()


def publish_config_variables(dbusservice):
    for variable, value in locals_copy.items():
        if variable.startswith("__"):
            continue
        if (
            isinstance(value, float)
            or isinstance(value, int)
            or isinstance(value, str)
            or isinstance(value, List)
        ):
            dbusservice.add_path(f"/Info/Config/{variable}", value)
