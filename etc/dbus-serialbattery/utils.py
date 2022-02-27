# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import logging
import serial
from time import sleep
from struct import *

# Logging
logging.basicConfig()
logger = logging.getLogger("SerialBattery")
logger.setLevel(logging.WARNING)

# Constants - Need to dynamically get them in future
DRIVER_VERSION = 0.10
DRIVER_SUBVERSION = ''
zero_char = chr(48)
degree_sign = u'\N{DEGREE SIGN}'
# Cell min/max voltages - used with the cell count to get the min/max battery voltage
MIN_CELL_VOLTAGE = 3.1
MAX_CELL_VOLTAGE = 3.45
# battery Current limits
MAX_BATTERY_CURRENT = 50.0
MAX_BATTERY_DISCHARGE_CURRENT = 60.0
# Battery capacity (amps)
BATTERY_CAPACITY = 50
# Invert Battery Current. Default non-inverted. Set to -1 to invert
INVERT_CURRENT_MEASUREMENT = 1
# Set of SoC percentages to report on dbus. The more you specify the more it will impact system performance.
#TIME_TO_SOC_POINTS = [100, 95, 90, 85, 80, 75, 70, 65, 60, 55, 50, 45, 40, 35, 30, 25, 20, 15, 10, 5, 0]		# Every 5% SoC
#TIME_TO_SOC_POINTS = []	                # No data set
TIME_TO_SOC_POINTS = [100, 95, 90, 85, 75, 50, 25, 20, 10, 0]
# Specify TimeToSoc value type:
#TIME_TO_SOC_VALUE_TYPE = 1        # Seconds
#TIME_TO_SOC_VALUE_TYPE = 2        # Time string HH:MN:SC
TIME_TO_SOC_VALUE_TYPE = 3        # Both Seconds and time str "<seconds> [days, HR:MN:SC]"
# Specify how many loop cycles between each TimeToSoc updates
TIME_TO_SOC_LOOP_CYCLES = 5
# Include TimeToSoC points when moving away from the SoC point.  These will be as negative time. Disabling this improves performance slightly.
TIME_TO_SOC_INC_FROM = False
#TIME_TO_SOC_INC_FROM = True
# Select the format of cell data presented on dbus.
BATTERY_CELL_DATA_FORMAT = 1                   # Format: /Voltages/Cell# (also available for display on Remote Console)
#BATTERY_CELL_DATA_FORMAT = 2                   # Format: /Cell/#/Volts
#BATTERY_CELL_DATA_FORMAT = 3                   # Both formats 1 and 2


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
                    logger.error(">>> ERROR: No reply - returning")
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
                    logger.error(">>> ERROR: No reply - returning")
                    return False

            return data

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
                #logger.error(">>> ERROR: No reply - returning")
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
        
