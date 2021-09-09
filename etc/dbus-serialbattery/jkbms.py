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

        # init the cell array
        for c in range(self.cell_count):
          self.cells.append(Cell(False))

        self.hardware_version = "JKBMS " + str(self.cell_count) + " cells"
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

        self.cell_count = unpack_from('>H', self.get_data(status_data, b'\x8A', 2))[0]

        # cell voltages
        cellbyte_count = unpack_from('>B', self.get_data(status_data, b'\x79', 1))[0]
        if cellbyte_count == 3*self.cell_count and self.cell_count == len(self.cells):
            celldata =  self.get_data(status_data, b'\x79', 1 + cellbyte_count)
            for c in range(self.cell_count):
                self.cells[c].voltage = unpack_from('>xH', celldata, c * 3 + 1)[0]/1000
        
        temp1 =  unpack_from('>H', self.get_data(status_data, b'\x81', 2))[0] 
        temp2 =  unpack_from('>H', self.get_data(status_data, b'\x82', 2))[0] 
        self.to_temp(1, temp1 if temp1 <= 100 else 100 - temp1)
        self.to_temp(2, temp2 if temp2 <= 100 else 100 - temp2)
        
        voltage = unpack_from('>H', self.get_data(status_data, b'\x83', 2))[0]
        self.voltage = voltage / 100

        current = unpack_from('>H', self.get_data(status_data, b'\x84', 2))[0]
        self.current = current / -100 if current < self.CURRENT_ZERO_CONSTANT else (current - self.CURRENT_ZERO_CONSTANT) / 100

        self.soc =  unpack_from('>B', self.get_data(status_data, b'\x85', 1))[0] 

        self.cycles =  unpack_from('>H', self.get_data(status_data, b'\x87', 2))[0] 

        self.capacity = unpack_from('>L', self.get_data(status_data, b'\xAA', 4))[0] 
        self.capacity_remain = unpack_from('>L', self.get_data(status_data, b'\x89', 4))[0]
        
        self.to_fet_bits(unpack_from('>H', self.get_data(status_data, b'\x8C', 2))[0] )

        # self.production
        # self.to_cell_bits(balance, balance2)
        # self.version = float(str(version >> 4 & 0x0F) + "." + str(version & 0x0F))
        # self.to_fet_bits(fet)
        # self.to_protection_bits(protection)


        # logger.info(self.hardware_version)
        return True
       
    def to_fet_bits(self, byte_data):
        tmp = bin(byte_data)[2:].rjust(2, zero_char)
        self.charge_fet = is_bit_set(tmp[1])
        self.discharge_fet = is_bit_set(tmp[0])

    def to_protection_bits(self, byte_data):
        pos=13
        tmp = bin(byte_data)[15-pos:].rjust(pos + 1, zero_char)
        logger.info(tmp)
        self.protection.soc_low = 2 if is_bit_set(tmp[pos-0]) else 0
        self.protection.set_IC_inspection = 2 if is_bit_set(tmp[pos-1]) else 0 # BMS over temp
        self.protection.voltage_high = 2 if is_bit_set(tmp[pos-2]) else 0
        self.protection.voltage_low = 2 if is_bit_set(tmp[pos-3]) else 0
        self.protection.current_over = 1 if is_bit_set(tmp[pos-5]) else 0
        self.protection.current_under = 1 if is_bit_set(tmp[pos-6]) else 0
        self.protection.cell_imbalance = 2 if is_bit_set(tmp[pos-7]) else 1 if is_bit_set(tmp[pos-10]) else 0
        self.protection.voltage_cell_low = 2 if is_bit_set(tmp[pos-11]) else 0        
        # there is just a BMS and Battery temp alarm (not high/low)
        self.protection.temp_high_charge = 1 if is_bit_set(tmp[pos-4]) or is_bit_set(tmp[pos-8]) else 0
        self.protection.temp_low_charge = 1 if is_bit_set(tmp[pos-4]) or is_bit_set(tmp[pos-8]) else 0
        self.protection.temp_high_discharge = 1 if is_bit_set(tmp[pos-4]) or is_bit_set(tmp[pos-8]) else 0
        self.protection.temp_low_discharge = 1 if is_bit_set(tmp[pos-4]) or is_bit_set(tmp[pos-8]) else 0

        
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
            logger.error(">>> ERROR: Incorrect Reply ")
            return False
