# -*- coding: utf-8 -*-
import logging
import serial
from time import sleep
from struct import *

# Logging
logging.basicConfig()
logger = logging.getLogger("SerialBattery")
logger.setLevel(logging.INFO)

# battery types
# if not specified: baud = 9600
battery_types = [
    {'bms' : "LltJbd"},
    {'bms' : "Ant", "baud" : 19200},
    {"bms" : "Daly", "address" : b"\x40"},
    {"bms" : "Daly", "address" : b"\x80"},
    {"bms" : "Jkbms", "baud" : 115200},
    {"bms" : "Jkbms_Ble" "address" : "C8:47:8C:E4:54:0E"},
    {"bms" : "Sinowealth"},
    {"bms" : "Lifepower"},
    {"bms" : "Renogy", "address": b"\x30"},
    {"bms" : "Renogy", "address": b"\xF7"},
#    {"bms" : "Revov"},
    {"bms" : "Ecs", "baud" : 19200},
#    {"bms" : "MNB"},
]

# Constants - Need to dynamically get them in future
DRIVER_VERSION = 0.14
DRIVER_SUBVERSION = '~3' 
zero_char = chr(48)
degree_sign = u'\N{DEGREE SIGN}'

# Choose the mode for voltage / current limitations
LIMITATION_MODE = "Classic"        # Classic Mode, limitations depending on State of Charge (SoC)
# LIMITATION_MODE = "WaldemarFech"    # WaldemarFech-Mode, limitations depending on min / max cell-voltage

######### WaldemarFech MODE #########
# Description:
# Maximal charge / discharge current will be in-/decreased depending on min- and max-cell-voltages and temperature
# Example: 18cells * 3.55V/cell = 63.9V max charge voltage. 18 * 2.7V = 48,6V min discharge voltage
#          ... but the (dis)charge current will be (in-/)decreased, if even ONE SINGLE BATTERY CELL reaches the limits
#          Also the temperature limit will be monitored to control the currents. If there are two temperature senors,
#          then the worst case will be calculated and the more secure lower current will be set.
if LIMITATION_MODE == "WaldemarFech":
    # Charge current control management referring to cell-voltage enable (True/False).
    CCCM_CV_ENABLE = True
    # Discharge current control management referring to cell-voltage enable (True/False).
    DCCM_CV_ENABLE = True
    # Charge current control management referring to temperature enable (True/False).
    CCCM_T_ENABLE = True
    # Charge current control management referring to temperature enable (True/False).
    DCCM_T_ENABLE = True
    # Charge voltage control management enable (True/False). Lower Charge-Voltage if Battery-Cell goes too high
    CVCM_ENABLE = True

    # Set Steps to reduce battery current. The current will be changed linear between those steps
    CELL_VOLTAGES_WHILE_CHARGING         = [3.55, 3.50, 3.45, 3.30]
    MAX_CHARGE_CURRENT_CV                = [   0,    2,  30,  60]

    CELL_VOLTAGES_WHILE_DISCHARGING      = [2.70, 2.80, 2.90, 3.10]
    MAX_DISCHARGE_CURRENT_CV             = [   0,    5,  30,  60]

    TEMPERATURE_LIMITS_WHILE_CHARGING    = [55, 40,  35,   5,  2, 0]
    MAX_CHARGE_CURRENT_T                 = [ 0, 28, 60, 60, 28, 0]

    TEMPERATURE_LIMITS_WHILE_DISCHARGING = [55, 40,  35,   5,  0, -20]
    MAX_DISCHARGE_CURRENT_T              = [ 0, 28, 60, 60, 28,   0]

    # if the cell voltage reaches 3.55V, then reduce current battery-voltage by 0.01V
    # if the cell voltage goes over 3.6V, then the maximum penalty will not be exceeded
    # there will be a sum of all penalties for each cell, which exceeds the limits
    PENALTY_AT_CELL_VOLTAGE  = [3.55, 3.6]
    PENALTY_BATTERY_VOLTAGE  = [0.01, 2.0]  # this voltage will be subtracted

    ### better don't change the following lines, when you don't know what you're doing
    # Cell min/max voltages - used with the cell count to get the min/max battery voltage
    MIN_CELL_VOLTAGE = CELL_VOLTAGES_WHILE_DISCHARGING[0]   # to calculate absolute minimum battery voltage
    MAX_CELL_VOLTAGE = CELL_VOLTAGES_WHILE_CHARGING[0]      # to calculate absolute maximum battery voltage
    # the following lines are for old-code compatibility - just let them unchanged
    MAX_BATTERY_CHARGE_CURRENT = max(MAX_CHARGE_CURRENT_CV)
    MAX_BATTERY_DISCHARGE_CURRENT = max(MAX_DISCHARGE_CURRENT_CV)




######### CLASSIC MODE #########
# Description:
# Maximal charge / discharge current will be increased / decreased depending on State of Charge, see CC_SOC_LIMIT1 etc.
# The State of Charge (SoC) will be calculated as the product of the cell-count and min/max-cell-voltages - these are the lower and upper voltage limits.
# Example: 16cells * 3.45V/cell = 55,2V max charge voltage. 16*2.9V = 46,4V min discharge voltage
if LIMITATION_MODE == "Classic":
    # Cell min/max voltages - used with the cell count to get the min/max battery voltage
    MIN_CELL_VOLTAGE = 2.9
    MAX_CELL_VOLTAGE = 3.45
    FLOAT_CELL_VOLTAGE = 3.35
    MAX_VOLTAGE_TIME_SEC = 15*60
    SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT = 90

    # battery Current limits
    MAX_BATTERY_CHARGE_CURRENT = 50.0
    MAX_BATTERY_DISCHARGE_CURRENT = 60.0

    # Charge current control management enable (True/False).
    CCCM_ENABLE = True
    # Discharge current control management enable (True/False).
    DCCM_ENABLE = True

    #charge current soc limits
    CC_SOC_LIMIT1 = 98
    CC_SOC_LIMIT2 = 95
    CC_SOC_LIMIT3 = 91

    #charge current limits
    CC_CURRENT_LIMIT1 = 5
    CC_CURRENT_LIMIT2 = MAX_BATTERY_CHARGE_CURRENT/4
    CC_CURRENT_LIMIT3 = MAX_BATTERY_CHARGE_CURRENT/2

    #discharge current soc limits
    DC_SOC_LIMIT1 = 10
    DC_SOC_LIMIT2 = 20
    DC_SOC_LIMIT3 = 30

    #discharge current limits
    DC_CURRENT_LIMIT1 = 5
    DC_CURRENT_LIMIT2 = MAX_BATTERY_DISCHARGE_CURRENT/4
    DC_CURRENT_LIMIT3 = MAX_BATTERY_DISCHARGE_CURRENT/2

    # Charge voltage control management enable (True/False).
    CVCM_ENABLE = False

# Simulate Midpoint graph (True/False).
MIDPOINT_ENABLE = False

#soc low levels
SOC_LOW_WARNING = 20
SOC_LOW_ALARM = 10

# Daly settings
# Battery capacity (amps) if the BMS does not support reading it 
BATTERY_CAPACITY = 50
# Invert Battery Current. Default non-inverted. Set to -1 to invert
INVERT_CURRENT_MEASUREMENT = 1

# TIME TO SOC settings [Valid values 0-100, but I don't recommend more that 20 intervals]
# Set of SoC percentages to report on dbus. The more you specify the more it will impact system performance.
# TIME_TO_SOC_POINTS = [100, 95, 90, 85, 80, 75, 70, 65, 60, 55, 50, 45, 40, 35, 30, 25, 20, 15, 10, 5, 0]		# Every 5% SoC
# TIME_TO_SOC_POINTS = [100, 95, 90, 85, 75, 50, 25, 20, 10, 0]
TIME_TO_SOC_POINTS = []	# No data set to disable
# Specify TimeToSoc value type: [Valid values 1,2,3]
# TIME_TO_SOC_VALUE_TYPE = 1      # Seconds
# TIME_TO_SOC_VALUE_TYPE = 2      # Time string HH:MN:SC
TIME_TO_SOC_VALUE_TYPE = 3        # Both Seconds and time str "<seconds> [days, HR:MN:SC]"
# Specify how many loop cycles between each TimeToSoc updates
TIME_TO_SOC_LOOP_CYCLES = 5
# Include TimeToSoC points when moving away from the SoC point. [Valid values True,False] 
# These will be as negative time. Disabling this improves performance slightly.
TIME_TO_SOC_INC_FROM = False


# Select the format of cell data presented on dbus. [Valid values 0,1,2,3]
# 0 Do not publish all the cells (only the min/max cell data as used by the default GX)
# 1 Format: /Voltages/Cell# (also available for display on Remote Console)
# 2 Format: /Cell/#/Volts
# 3 Both formats 1 and 2
BATTERY_CELL_DATA_FORMAT = 1

# Settings for ESC GreenMeter and Lipro devices
GREENMETER_ADDRESS = 1
LIPRO_START_ADDRESS = 2
LIPRO_END_ADDRESS = 4
LIPRO_CELL_COUNT = 15

def constrain(val, min_val, max_val):
    if min_val > max_val:
        min_val, max_val = max_val, min_val
    return min(max_val, max(min_val, val))

def mapRange(inValue, inMin, inMax, outMin, outMax):
    return outMin + (((inValue - inMin) / (inMax - inMin)) * (outMax - outMin))

def mapRangeConstrain(inValue, inMin, inMax, outMin, outMax):
    return constrain(mapRange(inValue, inMin, inMax, outMin, outMax), outMin, outMax)

def calcLinearRelationship(inValue, inArray, outArray):
    if inArray[0] < inArray[-1]:    # change compare-direction in array
        return calcLinearRelationship(inValue, inArray[::-1], outArray[::-1])
    else:
        upperIN  = inArray[0]
        upperOUT = outArray[0]
        lowerIN  = inArray[-1]  # last element in array
        lowerOUT = outArray[-1]
        outValue = 0

        if inValue >= upperIN:
            outValue = upperOUT
        elif inValue <= lowerIN:
            outValue = lowerOUT
        else:  # else calculate linear current between the setpoints
            for pos in range(1, len(inArray)):
                upperIN  = inArray[pos - 1]  # begin with pos 0 as max value
                upperOUT = outArray[pos - 1]
                lowerIN  = inArray[pos]
                lowerOUT = outArray[pos]
                if upperIN >= inValue >= lowerIN:
                    outValue = mapRangeConstrain(inValue, lowerIN, upperIN, lowerOUT, upperOUT)

    return outValue

def is_bit_set(tmp):
    return False if tmp == zero_char else True

def kelvin_to_celsius(kelvin_temp):
    return kelvin_temp - 273.1

def format_value(value, prefix, suffix):
    return None if value is None else ('' if prefix is None else prefix) + \
                                      str(value) + \
                                      ('' if suffix is None else suffix)

def read_serial_data(command, port, baud, length_pos, length_check, length_fixed=None, length_size=None):
    try:
        with serial.Serial(port, baudrate=baud, timeout=0.1) as ser:
            return read_serialport_data(ser, command, length_pos, length_check, length_fixed, length_size)

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

# Read data from previously openned serial port
def read_serialport_data(ser, command, length_pos, length_check, length_fixed=None, length_size=None):
    try:
        ser.flushOutput()
        ser.flushInput()
        ser.write(command)

        length_byte_size = 1
        if length_size is not None: 
            if length_size.upper() == 'H':
                length_byte_size = 2
            elif length_size.upper() == 'I' or length_size.upper() == 'L':
                length_byte_size = 4

        count = 0
        toread = ser.inWaiting()

        while toread < (length_pos+length_byte_size):
            sleep(0.005)
            toread = ser.inWaiting()
            count += 1
            if count > 50:
                logger.error(">>> ERROR: No reply - returning")
                return False
                
        #logger.info('serial data toread ' + str(toread))
        res = ser.read(toread)
        if length_fixed is not None:
            length = length_fixed
        else:
            if len(res) < (length_pos+length_byte_size):
                logger.error(">>> ERROR: No reply - returning [len:" + str(len(res)) + "]")
                return False
            length_size = length_size if length_size is not None else 'B'
            length = unpack_from('>'+length_size, res,length_pos)[0]
            
        #logger.info('serial data length ' + str(length))

        count = 0
        data = bytearray(res)
        while len(data) <= length + length_check:
            res = ser.read(length + length_check)
            data.extend(res)
            #logger.info('serial data length ' + str(len(data)))
            sleep(0.005)
            count += 1
            if count > 150:
                logger.error(">>> ERROR: No reply - returning [len:" + str(len(data)) + "/" + str(length + length_check) + "]")
                return False

        return data

    except serial.SerialException as e:
        logger.error(e)
        return False
