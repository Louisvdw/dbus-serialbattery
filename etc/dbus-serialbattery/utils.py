# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import logging
import serial
from time import sleep
from struct import *

# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Constants - Need to dynamically get them in future
DRIVER_VERSION = 0.6
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

def read_serial_data(command, port, baud, length_pos, length_check, length_fixed):
    try:
        with serial.Serial(port, baudrate=baud, timeout=0.1) as ser:
            ser.flushOutput()
            ser.flushInput()
            ser.write(command)

            count = 0
            toread = ser.inWaiting()

            while toread < (length_pos+1):
                sleep(0.005)
                toread = ser.inWaiting()
                count += 1
                if count > 50:
                    logger.error(">>> ERROR: No reply - returning")
                    return False
                    # raise Exception("No reply from {}".format(port))
            #logger.info('serial data toread ' + str(toread))
            res = ser.read(toread)
            length = length_fixed if length_fixed is not None else unpack_from('B', res,length_pos)[0]
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