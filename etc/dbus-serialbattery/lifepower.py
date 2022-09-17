# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from battery import Protection, Battery, Cell
from utils import *
from struct import *


class Lifepower(Battery):

    def __init__(self, port, baud):
        super(Lifepower, self).__init__(port, baud)
        self.type = self.BATTERYTYPE

    command_general = b"\x7E\x01\x01\x00\xFE\x0D"
    balancing = 0
    BATTERYTYPE = "EG4 Lifepower"
    LENGTH_CHECK = 5
    LENGTH_POS = 3
    LENGTH_FIXED = None

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
        self.version = "EG4 BMS V1.0"
        logger.info(self.hardware_version)
        return True

    def refresh_data(self):
        # call all functions that will refresh the battery data.
        # This will be called for every iteration (1 second)
        # Return True if success, False for failure
        return self.read_status_data()

    def read_status_data(self):
        status_data = self.read_serial_data_eg4(self.command_general)
        # check if connection success
        if status_data is False:
            return False

        # Data pulled from https://github.com/slim-bean/powermon

        groups = []
        i = 4
        for j in range(0,10):
            # groups are formatted like:
            # {group number} {length} ...length shorts...
            # So the first group might be:
            # 01 02 0a 0b 0c 0d
            group_len = status_data[i+1]
            end = i + 2 + (group_len*2)
            group_payload = status_data[i+2:end]
            groups.append([unpack_from('>H', group_payload, i)[0] for i in range(0, len(group_payload), 2)])

            i = end

        # Cells
        self.cell_count = len(groups[0])
        self.max_battery_voltage = MAX_CELL_VOLTAGE * self.cell_count
        self.min_battery_voltage = MIN_CELL_VOLTAGE * self.cell_count

        self.cells = [Cell(True) for _ in range(0, self.cell_count)]
        for i, cell in enumerate(self.cells):
            cell.voltage = groups[0][i] / 1000
        
        # Current
        self.current = groups[1][0] / 100

        # State of charge
        self.soc = groups[2][0] / 100

        # Full battery capacity
        self.capacity = groups[3][0] / 100

        # Temperature
        self.temp1 = groups[4][0]

        # TODO Alarms
        
        # Cycle counter
        self.cycles = groups[6][0]

        # Voltage
        self.voltage = groups[7][0] / 100

        # TODO State of health

        self.hardware_version = "EG4 Lifepower " + str(self.cell_count) + " cells"
        
        return True
        
    def get_balancing(self): 
        return 1 if self.balancing or self.balancing == 2 else 0

    def read_serial_data_eg4(self, command):
        # use the read_serial_data() function to read the data and then do BMS spesific checks (crc, start bytes, etc)
        data = read_serial_data(command, self.port, self.baud_rate,
                                self.LENGTH_POS, self.LENGTH_CHECK, self.LENGTH_FIXED)
        if data is False:
            logger.error(">>> ERROR: Incorrect Data")
            return False

        # 0x0D always terminates the response
        if data[-1] == 13:
            return data
        else:
            logger.error(">>> ERROR: Incorrect Reply")
            return False
