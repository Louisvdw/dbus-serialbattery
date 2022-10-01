# -*- coding: utf-8 -*-
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
    LENGTH_SIZE = 'H'
    CURRENT_ZERO_CONSTANT = 32768
    command_status = b"\x4E\x57\x00\x13\x00\x00\x00\x00\x06\x03\x00\x00\x00\x00\x00\x00\x68\x00\x00\x01\x29"

    def test_connection(self):
        # call a function that will connect to the battery, send a command and retrieve the result.
        # The result or call should be unique to this BMS. Battery name or version, etc.
        # Return True if success, False for failure
        result = False
        try:
            result = self.read_status_data()
        except:
            pass

        return result

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

    def get_data(self, bytes, idcode, start, length):
        # logger.debug("start "+str(start) + " length " + str(length))
        # logger.debug(binascii.hexlify(bytearray(bytes[start:start + 1 + length])).decode('ascii'))
        start = bytes.find(idcode, start, start + 1 + length)
        if start < 0: return False
        return bytes[start+1:start+length+1]


    def read_status_data(self):
        status_data = self.read_serial_data_jkbms(self.command_status)
        # check if connection success
        if status_data is False:
            return False


        # cell voltages
        offset = 1
        cellbyte_count = unpack_from('>B', self.get_data(status_data, b'\x79', offset, 1))[0]

        offset = cellbyte_count + 30
        self.cell_count = unpack_from('>H', self.get_data(status_data, b'\x8A', offset, 2))[0]

        if cellbyte_count == 3*self.cell_count and self.cell_count == len(self.cells):
            offset = 1
            celldata =  self.get_data(status_data, b'\x79', offset, 1 + cellbyte_count)
            for c in range(self.cell_count):
                self.cells[c].voltage = unpack_from('>xH', celldata, c * 3 + 1)[0]/1000
        
        offset = cellbyte_count + 6
        temp1 =  unpack_from('>H', self.get_data(status_data, b'\x81', offset, 2))[0] 
        offset = cellbyte_count + 9
        temp2 =  unpack_from('>H', self.get_data(status_data, b'\x82', offset, 2))[0] 
        self.to_temp(1, temp1 if temp1 <= 100 else 100 - temp1)
        self.to_temp(2, temp2 if temp2 <= 100 else 100 - temp2)
        
        offset = cellbyte_count + 12
        voltage = unpack_from('>H', self.get_data(status_data, b'\x83', offset, 2))[0]
        self.voltage = voltage / 100

        offset = cellbyte_count + 15
        current = unpack_from('>H', self.get_data(status_data, b'\x84', offset, 2))[0]
        self.current = current / -100 if current < self.CURRENT_ZERO_CONSTANT else (current - self.CURRENT_ZERO_CONSTANT) / 100

        offset = cellbyte_count + 18
        self.soc =  unpack_from('>B', self.get_data(status_data, b'\x85', offset, 1))[0] 

        offset = cellbyte_count + 22
        self.cycles =  unpack_from('>H', self.get_data(status_data, b'\x87', offset, 2))[0] 

        # offset = cellbyte_count + 25
        # self.capacity_remain = unpack_from('>L', self.get_data(status_data, b'\x89', offset, 4))[0]
        offset = cellbyte_count + 121
        self.capacity = unpack_from('>L', self.get_data(status_data, b'\xAA', offset, 4))[0] 
        
        offset = cellbyte_count + 33
        self.to_protection_bits(unpack_from('>H', self.get_data(status_data, b'\x8B', offset, 2))[0] )
        offset = cellbyte_count + 36
        self.to_fet_bits(unpack_from('>H', self.get_data(status_data, b'\x8C', offset, 2))[0] )

        offset = cellbyte_count + 155
        self.production = unpack_from('>8s', self.get_data(status_data, b'\xB4', offset, 8))[0].decode()
        offset = cellbyte_count + 174
        self.version = unpack_from('>15s', self.get_data(status_data, b'\xB7', offset, 15))[0].decode()

        # logger.info(self.hardware_version)
        return True
       
    def to_fet_bits(self, byte_data):
        tmp = bin(byte_data)[2:].rjust(2, zero_char)
        self.charge_fet = is_bit_set(tmp[1])
        self.discharge_fet = is_bit_set(tmp[0])

    def to_protection_bits(self, byte_data):
        pos=13
        tmp = bin(byte_data)[15-pos:].rjust(pos + 1, zero_char)
        # logger.debug(tmp)
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
        terminal = unpack_from('>L', data[4:])[0]
        cmd, src, tt = unpack_from('>bbb', data[8:])
        frame = unpack_from('>H', data[-9:])[0]
        end, crc_hi, crc_lo = unpack_from('>BHH', data[-5:])

        s = sum(data[0:-4])
        # logger.debug('S%d C%d C%d' % (s, crc_lo, crc_hi))
        # logger.debug('T%d C%d S%d F%d TT%d' % (terminal, cmd, src, frame, tt))

        if start == 0x4E57 and end == 0x68 and s == crc_lo:
            return data[10:length-19]
        elif s != crc_lo:
            logger.error('CRC checksum mismatch: Expected 0x%04x, Got 0x%04x' % (crc_lo, s))
            return False
        else:
            logger.error(">>> ERROR: Incorrect Reply ")
            return False

            