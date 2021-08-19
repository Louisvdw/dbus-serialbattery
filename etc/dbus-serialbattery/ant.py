# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from battery import Protection, Battery, Cell
from utils import *
from struct import *


class Ant(Battery):

    def __init__(self, port, baud):
        super(Ant, self).__init__(port, baud)
        self.type = self.BATTERYTYPE

    command_general = b"\xDB\xDB\x00\x00\x00\x00"
    BATTERYTYPE = "ANT"
    LENGTH_CHECK = 4
    LENGTH_POS = 3
    LENGTH_FIXED = 140

    def test_connection(self):
        # call a function that will connect to the battery, send a command and retrieve the result.
        # The result or call should be unique to this BMS. Battery name or version, etc.
        # Return True if success, False for failure
        return self.read_status_data()

    def get_settings(self):
        # After successful  connection get_settings will be call to set up the battery.
        # Set the current limits, populate cell count, etc
        # Return True if success, False for failure
        self.max_battery_current = MAX_BATTERY_CURRENT
        self.max_battery_discharge_current = MAX_BATTERY_DISCHARGE_CURRENT
        return True

    def refresh_data(self):
        # call all functions that will refresh the battery data.
        # This will be called for every iteration (1 second)
        # Return True if success, False for failure
        result = self.read_status_data()

        return result

    def read_status_data(self):
        status_data = self.read_serial_data_ant(self.command_general)
        # check if connection success
        if status_data is False:
            return False

        voltage = unpack_from('>H', status_data, 8)
        self.voltage = voltage[0]*0.1
        current, self.soc = unpack_from('>iH', status_data, 70)
        self.voltage = current*0.1 if current <= 2147483648 else -2147483648+current*0.1

        self.cell_count = 16
        self.max_battery_voltage = MAX_CELL_VOLTAGE * self.cell_count
        self.min_battery_voltage = MIN_CELL_VOLTAGE * self.cell_count

        self.hardware_version = "ANT BMS " + str(self.cell_count) + " cells"
        logger.info(self.hardware_version)
        return True

    def read_serial_data_ant(self, command):
        # use the read_serial_data() function to read the data and then do BMS spesific checks (crc, start bytes, etc)
        data = read_serial_data(command, self.port, self.baud_rate,
                                self.LENGTH_POS, self.LENGTH_CHECK, self.LENGTH_FIXED)
        if data is False:
            return False

        if data.length == self.LENGTH_FIXED:
            return data
        else:
            logger.error(">>> ERROR: Incorrect Reply")
            return False
