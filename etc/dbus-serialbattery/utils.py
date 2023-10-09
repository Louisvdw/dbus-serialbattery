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

PATH_CONFIG_DEFAULT = "config.default.ini"
PATH_CONFIG_USER = "config.ini"

config = configparser.ConfigParser()
path = Path(__file__).parents[0]
default_config_file_path = path.joinpath(PATH_CONFIG_DEFAULT).absolute().__str__()
custom_config_file_path = path.joinpath(PATH_CONFIG_USER).absolute().__str__()
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


# Constants
DRIVER_VERSION = "1.0.20231009dev"
zero_char = chr(48)
degree_sign = "\N{DEGREE SIGN}"

# get logging level from config file
if config["DEFAULT"]["LOGGING"] == "ERROR":
    logging.basicConfig(level=logging.ERROR)
elif config["DEFAULT"]["LOGGING"] == "WARNING":
    logging.basicConfig(level=logging.WARNING)
elif config["DEFAULT"]["LOGGING"] == "DEBUG":
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

# save config values to constants

# --------- Battery Current limits ---------
MAX_BATTERY_CHARGE_CURRENT = float(config["DEFAULT"]["MAX_BATTERY_CHARGE_CURRENT"])
MAX_BATTERY_DISCHARGE_CURRENT = float(
    config["DEFAULT"]["MAX_BATTERY_DISCHARGE_CURRENT"]
)

# --------- Cell Voltages ---------
MIN_CELL_VOLTAGE = float(config["DEFAULT"]["MIN_CELL_VOLTAGE"])
MAX_CELL_VOLTAGE = float(config["DEFAULT"]["MAX_CELL_VOLTAGE"])

FLOAT_CELL_VOLTAGE = float(config["DEFAULT"]["FLOAT_CELL_VOLTAGE"])
if FLOAT_CELL_VOLTAGE > MAX_CELL_VOLTAGE:
    FLOAT_CELL_VOLTAGE = MAX_CELL_VOLTAGE
    logger.error(
        ">>> ERROR: FLOAT_CELL_VOLTAGE is set to a value greater than MAX_CELL_VOLTAGE. Please check the configuration."
    )
if FLOAT_CELL_VOLTAGE < MIN_CELL_VOLTAGE:
    FLOAT_CELL_VOLTAGE = MIN_CELL_VOLTAGE
    logger.error(
        ">>> ERROR: FLOAT_CELL_VOLTAGE is set to a value less than MAX_CELL_VOLTAGE. Please check the configuration."
    )

SOC_RESET_VOLTAGE = float(config["DEFAULT"]["SOC_RESET_VOLTAGE"])
if SOC_RESET_VOLTAGE < MAX_CELL_VOLTAGE:
    SOC_RESET_VOLTAGE = MAX_CELL_VOLTAGE
    logger.error(
        ">>> ERROR: SOC_RESET_VOLTAGE is set to a value less than MAX_CELL_VOLTAGE. Please check the configuration."
    )
SOC_RESET_AFTER_DAYS = (
    int(config["DEFAULT"]["SOC_RESET_AFTER_DAYS"])
    if config["DEFAULT"]["SOC_RESET_AFTER_DAYS"] != ""
    else False
)

# --------- BMS disconnect behaviour ---------
BLOCK_ON_DISCONNECT = "True" == config["DEFAULT"]["BLOCK_ON_DISCONNECT"]

# --------- Charge mode ---------
LINEAR_LIMITATION_ENABLE = "True" == config["DEFAULT"]["LINEAR_LIMITATION_ENABLE"]
LINEAR_RECALCULATION_EVERY = int(config["DEFAULT"]["LINEAR_RECALCULATION_EVERY"])
LINEAR_RECALCULATION_ON_PERC_CHANGE = int(
    config["DEFAULT"]["LINEAR_RECALCULATION_ON_PERC_CHANGE"]
)

# --------- Charge Voltage limitation (affecting CVL) ---------
CVCM_ENABLE = "True" == config["DEFAULT"]["CVCM_ENABLE"]
CELL_VOLTAGE_DIFF_KEEP_MAX_VOLTAGE_UNTIL = float(
    config["DEFAULT"]["CELL_VOLTAGE_DIFF_KEEP_MAX_VOLTAGE_UNTIL"]
)
CELL_VOLTAGE_DIFF_TO_RESET_VOLTAGE_LIMIT = float(
    config["DEFAULT"]["CELL_VOLTAGE_DIFF_TO_RESET_VOLTAGE_LIMIT"]
)

MAX_VOLTAGE_TIME_SEC = int(config["DEFAULT"]["MAX_VOLTAGE_TIME_SEC"])
SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT = int(
    config["DEFAULT"]["SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT"]
)
CCCM_CV_ENABLE = "True" == config["DEFAULT"]["CCCM_CV_ENABLE"]
DCCM_CV_ENABLE = "True" == config["DEFAULT"]["DCCM_CV_ENABLE"]

CELL_VOLTAGES_WHILE_CHARGING = _get_list_from_config(
    "DEFAULT", "CELL_VOLTAGES_WHILE_CHARGING", lambda v: float(v)
)
if CELL_VOLTAGES_WHILE_CHARGING[0] < MAX_CELL_VOLTAGE:
    logger.error(
        ">>> ERROR: Maximum value of CELL_VOLTAGES_WHILE_CHARGING is set to a value lower than MAX_CELL_VOLTAGE. Please check the configuration."
    )
MAX_CHARGE_CURRENT_CV = _get_list_from_config(
    "DEFAULT",
    "MAX_CHARGE_CURRENT_CV_FRACTION",
    lambda v: MAX_BATTERY_CHARGE_CURRENT * float(v),
)

CELL_VOLTAGES_WHILE_DISCHARGING = _get_list_from_config(
    "DEFAULT", "CELL_VOLTAGES_WHILE_DISCHARGING", lambda v: float(v)
)
if CELL_VOLTAGES_WHILE_DISCHARGING[0] > MIN_CELL_VOLTAGE:
    logger.error(
        ">>> ERROR: Minimum value of CELL_VOLTAGES_WHILE_DISCHARGING is set to a value greater than MIN_CELL_VOLTAGE. Please check the configuration."
    )
MAX_DISCHARGE_CURRENT_CV = _get_list_from_config(
    "DEFAULT",
    "MAX_DISCHARGE_CURRENT_CV_FRACTION",
    lambda v: MAX_BATTERY_DISCHARGE_CURRENT * float(v),
)

# --------- Temperature limitation (affecting CCL/DCL) ---------
CCCM_T_ENABLE = "True" == config["DEFAULT"]["CCCM_T_ENABLE"]
DCCM_T_ENABLE = "True" == config["DEFAULT"]["DCCM_T_ENABLE"]

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
CCCM_SOC_ENABLE = "True" == config["DEFAULT"]["CCCM_SOC_ENABLE"]
DCCM_SOC_ENABLE = "True" == config["DEFAULT"]["DCCM_SOC_ENABLE"]

CC_SOC_LIMIT1 = float(config["DEFAULT"]["CC_SOC_LIMIT1"])
CC_SOC_LIMIT2 = float(config["DEFAULT"]["CC_SOC_LIMIT2"])
CC_SOC_LIMIT3 = float(config["DEFAULT"]["CC_SOC_LIMIT3"])

CC_CURRENT_LIMIT1 = MAX_BATTERY_CHARGE_CURRENT * float(
    config["DEFAULT"]["CC_CURRENT_LIMIT1_FRACTION"]
)
CC_CURRENT_LIMIT2 = MAX_BATTERY_CHARGE_CURRENT * float(
    config["DEFAULT"]["CC_CURRENT_LIMIT2_FRACTION"]
)
CC_CURRENT_LIMIT3 = MAX_BATTERY_CHARGE_CURRENT * float(
    config["DEFAULT"]["CC_CURRENT_LIMIT3_FRACTION"]
)

DC_SOC_LIMIT1 = float(config["DEFAULT"]["DC_SOC_LIMIT1"])
DC_SOC_LIMIT2 = float(config["DEFAULT"]["DC_SOC_LIMIT2"])
DC_SOC_LIMIT3 = float(config["DEFAULT"]["DC_SOC_LIMIT3"])

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
TIME_TO_GO_ENABLE = "True" == config["DEFAULT"]["TIME_TO_GO_ENABLE"]

# --------- Time-To-Soc ---------
TIME_TO_SOC_POINTS = _get_list_from_config(
    "DEFAULT", "TIME_TO_SOC_POINTS", lambda v: int(v)
)
TIME_TO_SOC_VALUE_TYPE = int(config["DEFAULT"]["TIME_TO_SOC_VALUE_TYPE"])
TIME_TO_SOC_RECALCULATE_EVERY = (
    int(config["DEFAULT"]["TIME_TO_SOC_RECALCULATE_EVERY"])
    if int(config["DEFAULT"]["TIME_TO_SOC_RECALCULATE_EVERY"]) > 5
    else 5
)
TIME_TO_SOC_INC_FROM = "True" == config["DEFAULT"]["TIME_TO_SOC_INC_FROM"]

# --------- Additional settings ---------
BMS_TYPE = _get_list_from_config("DEFAULT", "BMS_TYPE", lambda v: str(v))

EXCLUDED_DEVICES = _get_list_from_config(
    "DEFAULT", "EXCLUDED_DEVICES", lambda v: str(v)
)

CUSTOM_BATTERY_NAMES = _get_list_from_config(
    "DEFAULT", "CUSTOM_BATTERY_NAMES", lambda v: str(v)
)

# Auto reset SoC
# If on, then SoC is reset to 100%, if the value switches from absorption to float voltage
# Currently only working for Daly BMS and JK BMS BLE
AUTO_RESET_SOC = "True" == config["DEFAULT"]["AUTO_RESET_SOC"]

PUBLISH_CONFIG_VALUES = int(config["DEFAULT"]["PUBLISH_CONFIG_VALUES"])

BATTERY_CELL_DATA_FORMAT = int(config["DEFAULT"]["BATTERY_CELL_DATA_FORMAT"])

MIDPOINT_ENABLE = "True" == config["DEFAULT"]["MIDPOINT_ENABLE"]

TEMP_BATTERY = int(config["DEFAULT"]["TEMP_BATTERY"])

TEMP_1_NAME = config["DEFAULT"]["TEMP_1_NAME"]
TEMP_2_NAME = config["DEFAULT"]["TEMP_2_NAME"]
TEMP_3_NAME = config["DEFAULT"]["TEMP_3_NAME"]
TEMP_4_NAME = config["DEFAULT"]["TEMP_4_NAME"]

# --------- BMS specific settings ---------
SOC_LOW_WARNING = float(config["DEFAULT"]["SOC_LOW_WARNING"])
SOC_LOW_ALARM = float(config["DEFAULT"]["SOC_LOW_ALARM"])

# -- Daly settings
BATTERY_CAPACITY = float(config["DEFAULT"]["BATTERY_CAPACITY"])
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


# Publish config variables to dbus
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
