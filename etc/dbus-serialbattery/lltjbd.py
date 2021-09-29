# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from battery import Protection, Battery, Cell
from utils import *
from struct import *

class LltJbdProtection(Protection):

    def __init__(self):
        super(LltJbdProtection, self).__init__()
        self.voltage_high_cell = False
        self.voltage_low_cell = False
        self.short = False
        self.IC_inspection = False
        self.software_lock = False

    def set_voltage_high_cell(self, value):
        self.voltage_high_cell = value
        self.cell_imbalance = 2 if self.voltage_low_cell \
                                        or self.voltage_high_cell else 0

    def set_voltage_low_cell(self, value):
        self.voltage_low_cell = value
        self.cell_imbalance = 2 if self.voltage_low_cell \
                                        or self.voltage_high_cell else 0

    def set_short(self, value):
        self.short = value
        self.set_cell_imbalance(2 if self.short \
                                        or self.IC_inspection \
                                        or self.software_lock else 0)

    def set_ic_inspection(self, value):
        self.IC_inspection = value
        self.set_cell_imbalance(2 if self.short \
                                        or self.IC_inspection \
                                        or self.software_lock else 0)

    def set_software_lock(self, value):
        self.software_lock = value
        self.set_cell_imbalance(2 if self.short \
                                        or self.IC_inspection \
                                        or self.software_lock else 0)


class LltJbd(Battery):

    def __init__(self, port,baud):
        super(LltJbd, self).__init__(port,baud)
        self.protection = LltJbdProtection()
        self.type = self.BATTERYTYPE

# degree_sign = u'\N{DEGREE SIGN}'
    command_general = b"\xDD\xA5\x03\x00\xFF\xFD\x77"
    command_cell = b"\xDD\xA5\x04\x00\xFF\xFC\x77"
    command_hardware = b"\xDD\xA5\x05\x00\xFF\xFB\x77"
    BATTERYTYPE = "LLT/JBD"
    LENGTH_CHECK = 6
    LENGTH_POS = 3

    def test_connection(self):
        return self.read_hardware_data()

    def get_settings(self):
        self.read_gen_data()
        self.max_battery_current = MAX_BATTERY_CURRENT
        self.max_battery_discharge_current = MAX_BATTERY_DISCHARGE_CURRENT
        return True

    def refresh_data(self):
        result = self.read_gen_data()
        result = result and self.read_cell_data()
        return result

    def to_protection_bits(self, byte_data):
        tmp = bin(byte_data)[2:].rjust(13, zero_char)

        self.protection.voltage_high = 2 if is_bit_set(tmp[10]) else 0
        self.protection.voltage_low = 2 if is_bit_set(tmp[9]) else 0
        self.protection.temp_high_charge = 1 if is_bit_set(tmp[8]) else 0
        self.protection.temp_low_charge = 1 if is_bit_set(tmp[7]) else 0
        self.protection.temp_high_discharge = 1 if is_bit_set(tmp[6]) else 0
        self.protection.temp_low_discharge = 1 if is_bit_set(tmp[5]) else 0
        self.protection.current_over = 1 if is_bit_set(tmp[4]) else 0
        self.protection.current_under = 1 if is_bit_set(tmp[3]) else 0

        # Software implementations for low soc
        self.protection.soc_low = 2 if self.soc < 10 else 1 if self.soc < 20 else 0

        # extra protection flags for LltJbd
        self.protection.set_voltage_low_cell = is_bit_set(tmp[11])
        self.protection.set_voltage_high_cell = is_bit_set(tmp[12])
        self.protection.set_software_lock = is_bit_set(tmp[0])
        self.protection.set_IC_inspection = is_bit_set(tmp[1])
        self.protection.set_short = is_bit_set(tmp[2])

    def to_cell_bits(self, byte_data, byte_data_high):
        # clear the list
        for c in self.cells:
            self.cells.remove(c)
        # get up to the first 16 cells
        tmp = bin(byte_data)[2:].rjust(min(self.cell_count, 16), zero_char)
        for bit in reversed(tmp):
            self.cells.append(Cell(is_bit_set(bit)))
        # get any cells above 16
        if self.cell_count > 16:
            tmp = bin(byte_data_high)[2:].rjust(self.cell_count-16, zero_char)
            for bit in reversed(tmp):
                self.cells.append(Cell(is_bit_set(bit)))

    def to_fet_bits(self, byte_data):
        tmp = bin(byte_data)[2:].rjust(2, zero_char)
        self.charge_fet = is_bit_set(tmp[1])
        self.discharge_fet = is_bit_set(tmp[0])

    def read_gen_data(self):
        gen_data = self.read_serial_data_llt(self.command_general)
        # check if connect success
        if gen_data is False or len(gen_data) < 27:
            return False

        voltage, current, capacity_remain, capacity, self.cycles, self.production, balance, \
            balance2, protection, version, self.soc, fet, self.cell_count, self.temp_sensors, temp1, temp2 \
            = unpack_from('>HhHHHHhHHBBBBBHH', gen_data)
        self.voltage = voltage / 100
        self.current = current / 100
        self.capacity_remain = capacity_remain / 100
        self.capacity = capacity / 100
        self.to_temp(1, kelvin_to_celsius(temp1 / 10))
        self.to_temp(2, kelvin_to_celsius(temp2 / 10))
        self.to_cell_bits(balance, balance2)
        self.version = float(str(version >> 4 & 0x0F) + "." + str(version & 0x0F))
        self.to_fet_bits(fet)
        self.to_protection_bits(protection)
        self.max_battery_voltage = MAX_CELL_VOLTAGE * self.cell_count
        self.min_battery_voltage = MIN_CELL_VOLTAGE * self.cell_count

        return True

    def read_cell_data(self):
        cell_data = self.read_serial_data_llt(self.command_cell)
        # check if connect success
        if cell_data is False or len(cell_data) < self.cell_count*2:
            return False

        for c in range(self.cell_count):
            try:
                cell_volts = unpack_from('>H', cell_data, c * 2)
                if len(cell_volts) != 0:
                    self.cells[c].voltage = cell_volts[0] / 1000
            except struct.error:
                self.cells[c].voltage = 0
        return True

    def read_hardware_data(self):
        hardware_data = self.read_serial_data_llt(self.command_hardware)
        # check if connection success
        if hardware_data is False:
            return False

        self.hardware_version = unpack_from('>' + str(len(hardware_data)) + 's', hardware_data)[0]
        logger.debug(self.hardware_version)
        return True

    def read_serial_data_llt(self, command):
        data = read_serial_data(command, self.port, self.baud_rate, self.LENGTH_POS, self.LENGTH_CHECK)
        if data is False:
            return False

        start, flag, command_ret, length = unpack_from('BBBB', data)
        checksum, end = unpack_from('HB', data, length + 4)

        if end == 119:
            return data[4:length + 4]
        else:
            logger.error(">>> ERROR: Incorrect Reply")
            return False