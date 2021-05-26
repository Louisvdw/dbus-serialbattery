# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import logging
import serial
from time import sleep
from struct import *

# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

zero_char = chr(48)
def is_bit_set(tmp):
    return False if tmp == zero_char else True

def kelvin_to_celsius(kelvin_temp):
    return kelvin_temp - 273.1

def read_serial_data(command, port, baud, length_check=6):
    try:
        with serial.Serial(port, baudrate=baud, timeout=0.1) as ser:
            ser.flushOutput()
            ser.flushInput()
            ser.write(command)

            count = 0
            toread = ser.inWaiting()
            while toread < 4:
                sleep(0.01)
                toread = ser.inWaiting()
                count += 1
                if count > 50:
                    logger.error(">>> ERROR: No reply - returning")
                    return False
                    # raise Exception("No reply from {}".format(port))

            res = ser.read(toread)
            start, flag, command1, length = unpack_from('BBBB', res)

            data = bytearray(res)
            while len(data) <= length + length_check:
                res = ser.read(length+3)
                data.extend(res)
                sleep(0.2)

            checksum, end = unpack_from('HB', data, length+4)

            if end == 119:
                # logger.info("start=" + str(start))
                # logger.info("flag=" + str(flag))
                # logger.info("command=" + str(command1))
                # logger.info("data length=" + str(length))
                # logger.info("checksum=" + str(checksum))
                # logger.info("end=" + str(end))
                return data[4:length+4]
            else:
                logger.error(">>> ERROR: Incorrect Reply")
                return False
    except serial.SerialException as e:
        logger.error(e)
        return False