# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from battery import Protection, Battery, Cell
from utils import *
from struct import *

class Daly(Battery):

    def __init__(self, port,baud,address):
        super(Daly, self).__init__(port,baud)
        self.charger_connected = None
        self.load_connected = None
        self.command_address = address
    # command bytes [StartFlag=A5][Address=40][Command=94][DataLength=8][8x zero bytes][checksum]
    command_base = b"\xA5\x40\x94\x08\x00\x00\x00\x00\x00\x00\x00\x00\x81"
    command_soc = b"\x90"
    command_minmax_cell_volts = b"\x91"
    command_minmax_temp = b"\x92"
    command_fet = b"\x93"
    command_status = b"\x94"
    command_cell_volts = b"\x95"
    command_temp = b"\x96"
    command_cell_balance = b"\x97"
    command_alarm = b"\x98"
    BATTERYTYPE = "Daly"
    LENGTH_CHECK = 5
    LENGTH_POS = 3

    def test_connection(self):
        return self.read_status_data()

    def get_settings(self):
        self.type = self.BATTERYTYPE

        return True

    def refresh_data(self):
        result = self.read_soc_data()

        return result

    def read_status_data(self):
        status_data = self.read_serial_data_daly(self.command_status)
        # check if connection success
        if status_data is False:
            return False

        self.cell_count, self.temp_censors, self.charger_connected, self.load_connected, \
            state, self.cycles = unpack_from('>bb??bhx', status_data)

        self.hardware_version = "DalyBMS " + str(self.cell_count) + " cells"
        logger.info(self.hardware_version)
        return True

    def read_soc_data(self):
        soc_data = self.read_serial_data_daly(self.command_soc)
        # check if connection success
        if soc_data is False:
            return False

        voltage, current, soc = struct.unpack_from('>hxhh', status_data)
        self.voltage = voltage / 10
        self.current = (current- 30000) / 10
        self.soc = soc / 10
        return True

    def generate_command(self, command):
        buffer = bytearray(self.command_base)
        buffer[1] = self.command_address   # Always serial 40 for now
        buffer[2] = command
        buffer[12] = sum(buffer[:11]) & 0xFF   #checksum calc
        return buffer

    def read_serial_data_daly(self, command):
        data = read_serial_data(self.generate_command(command), self.port, self.baud_rate, self.LENGTH_POS, self.LENGTH_CHECK)
        if data is False:
            return False

        start, flag, command_ret, length = unpack_from('BBBB', data)
        checksum = sum(data[4:8]) & 0xFF

        if start == b"\xA5" and length == 8 and checksum == data[:-1]:
            return data[3:length]
        else:
            logger.error(">>> ERROR: Incorrect Reply")
            return False
