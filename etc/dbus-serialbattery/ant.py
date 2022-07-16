# -*- coding: utf-8 -*-
from battery import Protection, Battery, Cell
from utils import *
from struct import *


class Ant(Battery):

    def __init__(self, port, baud):
        super(Ant, self).__init__(port, baud)
        self.type = self.BATTERYTYPE

    command_general = b"\xDB\xDB\x00\x00\x00\x00"
    # command_capacity_low = b"\x5A\x5A\x1F\x00\x00\x1F"
    # command_capacity_high = b"\x5A\x5A\x20\x00\x00\x20"
    balancing = 0
    BATTERYTYPE = "ANT"
    LENGTH_CHECK = -1
    LENGTH_POS = 139
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
        self.version = "ANT BMS V2.0"
        logger.info(self.hardware_version)
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

        voltage = unpack_from('>H', status_data, 4)
        self.voltage = voltage[0]*0.1
        current, self.soc = unpack_from('>lB', status_data, 70)
        self.current = 0.0 if current == 0 else current / -10

        self.cell_count = unpack_from('>b', status_data, 123)[0]
        self.max_battery_voltage = MAX_CELL_VOLTAGE * self.cell_count
        self.min_battery_voltage = MIN_CELL_VOLTAGE * self.cell_count

        cell_max_no, cell_max_voltage, cell_min_no, cell_min_voltage = unpack_from('>bhbh', status_data, 115)
        self.cell_max_no = cell_max_no - 1
        self.cell_min_no = cell_min_no - 1
        self.cell_max_voltage = cell_max_voltage / 1000
        self.cell_min_voltage = cell_min_voltage / 1000
        
        capacity = unpack_from('>L', status_data, 75)
        self.capacity = capacity[0] / 1000000

        capacity_remain = unpack_from('>L', status_data, 79)
        self.capacity_remain = capacity_remain[0] / 1000000
        
        total_ah_drawn = unpack_from('>L', status_data, 83)
        self.total_ah_drawn = total_ah_drawn[0] / 1000 
        self.cycles = self.total_ah_drawn / self.capacity
        
        self.charge_fet, self.discharge_fet, self.balancing = unpack_from('>bbb',status_data, 103)

        self.temp1, self.temp2 = unpack_from('>bxb',status_data, 96)

        self.hardware_version = "ANT BMS " + str(self.cell_count) + " cells"
        
        # Alarms
        self.protection.voltage_high = 2 if self.charge_fet==2 else 0
        self.protection.voltage_low = 2 if self.discharge_fet==2 or self.discharge_fet==5 else 0
        self.protection.voltage_cell_low = 2 if self.cell_min_voltage < MIN_CELL_VOLTAGE - 0.1 else 1 if self.cell_min_voltage < MIN_CELL_VOLTAGE else 0
        self.protection.temp_high_charge = 1 if self.charge_fet==3 or self.charge_fet==6  else 0
        self.protection.temp_high_discharge = 1 if self.discharge_fet==7 or self.discharge_fet==6 else 0
        self.protection.current_over = 2 if self.charge_fet==3 else 0
        self.protection.current_under = 2 if self.discharge_fet==3 else 0
        
        return True
        
    def get_balancing(self): 
        return 1 if self.balancing or self.balancing == 2 else 0

    def read_serial_data_ant(self, command):
        # use the read_serial_data() function to read the data and then do BMS spesific checks (crc, start bytes, etc)
        data = read_serial_data(command, self.port, self.baud_rate,
                                self.LENGTH_POS, self.LENGTH_CHECK, self.LENGTH_FIXED)
        if data is False:
            logger.error(">>> ERROR: Incorrect Data")
            return False

        if len(data) == self.LENGTH_FIXED:
            return data
        else:
            logger.error(">>> ERROR: Incorrect Reply")
            return False
