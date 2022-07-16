# -*- coding: utf-8 -*-
from battery import Protection, Battery, Cell
from utils import *
import struct

class RenogyCell(Cell):
    temp = None

class Renogy(Battery):

    def __init__(self, port,baud):
        super(Renogy, self).__init__(port,baud)
        self.type = self.BATTERYTYPE

    BATTERYTYPE = "Renogy"
    LENGTH_CHECK = 4
    LENGTH_POS = 2

    # command bytes [Address field][Function code (03 = Read register)][Register Address (2 bytes)][Data Length (2 bytes)][CRC (2 bytes little endian)]
    # Battery addresses start at 0 ascii, 30 hex
    command_address = b"0"
    command_read = b"\x03"
    # Core data = voltage, temp, current, soc
    command_cell_count = b"\x13\x88\x00\x01"         #Register  5000
    command_cell_voltages = b"\x13\x89\x00\x04"      #Registers 5001-5004
    command_cell_temps = b"\x13\x9A\x00\x04"         #Registers 5018-5021
    command_total_voltage = b"\x13\xB3\x00\x01"      #Register  5043
    command_bms_temp1 = b"\x13\xAD\x00\x01"          #Register  5037
    command_bms_temp2 = b"\x13\xB0\x00\x01"          #Register  5040
    command_current = b"\x13\xB2\x00\x01"            #Register  5042 (signed int)
    command_capacity = b"\x13\xB6\x00\x02"           #Registers 5046-5047 (long)
    command_soc = b"\x13\xB2\x00\x04"                #Registers 5042-5045 (amps, volts, soc as long)
    # Battery info
    command_manufacturer = b"\x14\x0C\x00\x08"       #Registers 5132-5139 (8 byte string)
    command_model = b"\x14\x02\x00\x08"              #Registers 5122-5129 (8 byte string)
    command_serial_number = b"\x13\xF6\x00\x08"      #Registers 5110-5117 (8 byte string)
    command_firmware_version = b"\x14\x0A\x00\x02"   #Registers 5130-5131 (2 byte string)
    # BMS warning and protection config

    def test_connection(self):
        # call a function that will connect to the battery, send a command and retrieve the result.
        # The result or call should be unique to this BMS. Battery name or version, etc.
        # Return True if success, False for failure
        return self.read_gen_data()

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
        result = self.read_soc_data()
        result = result and self.read_cell_data()
        result = result and self.read_temp_data()

        return result

    def read_gen_data(self):
        model = self.read_serial_data_renogy(self.command_model)
        # check if connection success
        if model is False:
            return False
        model_num = unpack('16s',model)[0]
        self.hardware_version = "Renogy " + str(model_num)
        logger.info(self.hardware_version)

        self.temp_sensors = 2

        if self.cell_count is None:
            cc = self.read_serial_data_renogy(self.command_cell_count)
            self.cell_count = struct.unpack('>H',cc)[0]
            
            for c in range(self.cell_count):
                self.cells.append(RenogyCell(False))

        firmware = self.read_serial_data_renogy(self.command_firmware_version)
        firmware_major, firmware_minor = unpack_from('2s2s', firmware)
        self.version = float(str(firmware_major) + "." + str(firmware_minor))
        capacity = self.read_serial_data_renogy(self.command_capacity)
        self.capacity = unpack('>L',capacity)[0]
        return True

    def read_soc_data(self):
        soc_data = self.read_serial_data_renogy(self.command_soc)
        # check if connection success
        if soc_data is False:
            return False

        current, voltage, self.capacity_remain = unpack_from('>hhL', soc_data)
        self.current = current / 100
        self.voltage = voltage / 10
        self.soc = self.capacity_remain / self.capacity * 100
        return True

    def read_cell_data(self):
        cell_volt_data = self.read_serial_data_renogy(self.command_cell_voltages)
        cell_temp_data = self.read_serial_data_renogy(self.command_cell_temps)
        for c in range(self.cell_count):
            try:
                cell_volts = unpack_from('>H', cell_volt_data, c*2)
                cell_temp = unpack_from('>H', cell_temp_data, c*2)
                if len(cell_volts) != 0:
                    self.cells[c].voltage = cell_volts[0] / 10
                    self.cells[c].temp = cell_temp[0] / 10
            except struct.error:
                self.cells[c].voltage = 0
        return True

    def read_temp_data(self):
        temp1 = self.read_serial_data_renogy(self.command_bms_temp1)
        temp2 = self.read_serial_data_renogy(self.command_bms_temp2)
        if temp1 is False:
            return False
        self.temp1 = unpack('>H',temp1)[0] / 10
        self.temp2 = unpack('>H',temp2)[0] / 10
        
        return True

    def read_bms_config(self):
        return True

    def calc_crc(self, data):
        crc = 0xFFFF
        for pos in data:
            crc ^= pos 
            for i in range(8):
                if ((crc & 1) != 0):
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        return struct.pack('<H',crc)
    
    def generate_command(self, command):
        buffer = bytearray(self.command_address)
        buffer += self.command_read
        buffer += command
        buffer += self.calc_crc(buffer)

        return buffer

    def read_serial_data_renogy(self, command):
        # use the read_serial_data() function to read the data and then do BMS spesific checks (crc, start bytes, etc)
        data = read_serial_data(self.generate_command(command), self.port, self.baud_rate, self.LENGTH_POS, self.LENGTH_CHECK)
        if data is False:
            return False

        start, flag, length = unpack_from('BBB', data)
        checksum = unpack_from('>H', data, length + 3)

        if flag == 3:
            return data[3:length+3]
        else:
            logger.error(">>> ERROR: Incorrect Reply")
            return False