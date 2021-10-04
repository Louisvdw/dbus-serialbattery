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
DRIVER_VERSION = 0.9
DRIVER_SUBVERSION = ''
zero_char = chr(48)
degree_sign = u'\N{DEGREE SIGN}'
# Cell min/max voltages - used with the cell count to get the min/max battery voltage
MIN_CELL_VOLTAGE = 3.1
MAX_CELL_VOLTAGE = 3.45
# battery Current limits
MAX_BATTERY_CURRENT = 50.0
MAX_BATTERY_DISCHARGE_CURRENT = 60.0

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
        
