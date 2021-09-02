# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from battery import Protection, Battery, Cell
from utils import *
from struct import *

class Jkbms(Battery):

    def __init__(self, port,baud):
        super(Jkbms, self).__init__(port,baud)
        self.type = self.BATTERYTYPE

    BATTERYTYPE = "Jkbms"
    LENGTH_CHECK = 1
    LENGTH_POS = 2
    LENGTH_SIZE = '>H'
    CURRENT_ZERO_CONSTANT = 32768
    command_status = b"\x4E\x57\x00\x13\x00\x00\x00\x00\x06\x03\x00\x00\x00\x00\x00\x00\x68\x00\x00\x01\x29"

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
        self.max_battery_voltage = MAX_CELL_VOLTAGE * self.cell_count
        self.min_battery_voltage = MIN_CELL_VOLTAGE * self.cell_count
        return True

    def refresh_data(self):
        # call all functions that will refresh the battery data.
        # This will be called for every iteration (1 second)
        # Return True if success, False for failure
        result = self.read_status_data()

        return result

    def get_data(self, bytes, idcode, length):
        start = bytes.find(idcode)
        if start < 0: return False
        return bytes[start+1:start+length+1]


    def read_status_data(self):
        status_data = self.read_serial_data_jkbms(self.command_status)
        # check if connection success
        if status_data is False:
            return False

        cellbyte_count = unpack_from('>B', self.get_data(status_data, b'\x79', 1))[0]
        self.cell_count = cellbyte_count / 3
        
        voltage = unpack_from('>H', self.get_data(status_data, b'\x83', 2))[0]
        current = unpack_from('>H', self.get_data(status_data, b'\x84', 2))[0]
        self.soc =  unpack_from('>B', self.get_data(status_data, b'\x85', 1))[0] 

        self.voltage = voltage / 100
        self.current = current / -100 if current < self.CURRENT_ZERO_CONSTANT else (current - self.CURRENT_ZERO_CONSTANT) / 100

        # self.cell_count, self.temp_sensors, self.charger_connected, self.load_connected, \
        #     state, self.cycles = unpack_from('>bb??bhx', status_data)

        # self.hardware_version = "JKBMS " + str(self.cell_count) + " cells"
        # logger.info(self.hardware_version)
        return True

    def read_serial_data_jkbms(self, command):
        # use the read_serial_data() function to read the data and then do BMS spesific checks (crc, start bytes, etc)
        data = read_serial_data(command, self.port, self.baud_rate, self.LENGTH_POS, self.LENGTH_CHECK,None, self.LENGTH_SIZE)
        if data is False:
            return False

        start, length = unpack_from('>HH', data)
        end, crc = unpack_from('>BI', data[-5:])
        
        if start == 0x4E57 and end == 0x68:
            return data[10:length-19]
        else:
            logger.error(">>> ERROR: Incorrect Reply")
            return False
