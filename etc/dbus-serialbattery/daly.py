# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from battery import Protection, Battery, Cell
from utils import *
from struct import *
from math import sum

class Daly(Battery):

    def __init__(self, port,baud):
        super(Daly, self).__init__(port,baud)

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
    length_check = 5

    def test_connection(self):
        return self.read_status_data()

    def get_settings(self):
        self.type = self.BATTERYTYPE
        self.read_gen_data()
        return True

    def refresh_data(self):
        result = self.read_gen_data()
        # result = result and self.read_cell_data()
        return result



    def read_gen_data(self):
        # gen_data = read_serial_data(self.generate_command(self.command_status), self.port, self.baud_rate, self.length_check)
        # # check if connect success
        # if gen_data is False or len(gen_data) < 27:
        #     return False
        #

        return True

    def read_status_data(self):
        status_data = read_serial_data(self.generate_command(self.command_status), self.port, self.baud_rate, self.length_check)
        # check if connection success
        if status_data is False:
            return False

        self.hardware_version = unpack_from('>' + str(len(status_data)) + 's', status_data)[0]
        logger.info(self.hardware_version)
        return True

    def generate_command(self, command):
        buffer = self.command_base
        # buffer[1] = b"\x40"   # Always serial 40 for now
        buffer[2] = command
        buffer[12] = [sum(buffer[:11]) & 0xFF]   #crc calc
        return buffer

