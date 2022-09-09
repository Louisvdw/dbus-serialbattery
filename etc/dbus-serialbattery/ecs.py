# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from battery import Protection, Battery, Cell
from utils import *
from struct import *
import minimalmodbus

class Ecs(Battery):

    def __init__(self, port,baud):
        super(Ecs, self).__init__(port,baud)
        self.type = self.BATTERYTYPE

    BATTERYTYPE = "ECS_LiPro"
    GREENMETER_ADDRESS = 1
    GREENMETER_ID_500A = 500
    GREENMETER_ID_250A = 501
    GREENMETER_ID_125A = 502
    METER_SIZE = ""
    LIPRO_START_ADDRESS = 2
    LIPRO_END_ADDRESS = 4
    LIPRO_CELL_COUNT = 15

    def test_connection(self):
        # call a function that will connect to the battery, send a command and retrieve the result.
        # The result or call should be unique to this BMS. Battery name or version, etc.
        # Return True if success, False for failure
        
        # Trying to find Green Meter ID
        try:
            mbdev = minimalmodbus.Instrument(self.port, self.GREENMETER_ADDRESS)  
            mbdev.serial.parity = minimalmodbus.serial.PARITY_EVEN
            tmpId = mbdev.read_register(0, 0)
            if tmpId in range(self.GREENMETER_ID_500A,self.GREENMETER_ID_125A+1):
                if tmpId == self.GREENMETER_ID_500A:
                    self.METER_SIZE = "500A"
                if tmpId == self.GREENMETER_ID_250A:
                    self.METER_SIZE = "250A"
                if tmpId == self.GREENMETER_ID_125A:
                    self.METER_SIZE = "125A"
                return self.get_settings()
        except IOError:
            return False

    def get_settings(self):
        # After successful  connection get_settings will be call to set up the battery.
        # Set the current limits, populate cell count, etc
        # Return True if success, False for failure
        
        # Uncomment if BMS does not supply capacity
        self.max_battery_current = MAX_BATTERY_CURRENT
        self.max_battery_discharge_current = MAX_BATTERY_DISCHARGE_CURRENT
        self.cell_count = self.LIPRO_CELL_COUNT
        self.max_battery_voltage = MAX_CELL_VOLTAGE * self.cell_count
        self.min_battery_voltage = MIN_CELL_VOLTAGE * self.cell_count
        self.temp_sensors = 2

        return self.read_status_data()

    def refresh_data(self):
        # call all functions that will refresh the battery data.
        # This will be called for every iteration (1 second)
        # Return True if success, False for failure
        result = self.read_soc_data()
        # result = result and self.read_cell_data()

        return result

    def read_status_data(self):
        try:
            mbdev = minimalmodbus.Instrument(self.port, self.GREENMETER_ADDRESS)  
            mbdev.serial.parity = minimalmodbus.serial.PARITY_EVEN
            
            self.max_battery_discharge_current = abs(mbdev.read_register(30, 0, 3, True))
            self.max_battery_current = mbdev.read_register(31, 0, 3, True)
            self.capacity = mbdev.read_long(46, 3, False, minimalmodbus.BYTEORDER_LITTLE_SWAP)/1000
            self.production = mbdev.read_long(2, 3, False, minimalmodbus.BYTEORDER_LITTLE_SWAP)

            # for c in range(self.LIPRO_END_ADDRESS-self.LIPRO_START_ADDRESS+1):
            #     self.cells.append(Cell(False))

            self.hardware_version = "Greenmeter-" + self.METER_SIZE + " " + str(self.cell_count) + " cells"
            logger.info(self.hardware_version)

            return True
        except IOError:
            return False

    def read_soc_data(self):
        try:
            mbdev = minimalmodbus.Instrument(self.port, self.GREENMETER_ADDRESS)  
            mbdev.serial.parity = minimalmodbus.serial.PARITY_EVEN

            self.voltage = mbdev.read_long(108, 3, False, minimalmodbus.BYTEORDER_LITTLE_SWAP) / 1000
            self.current = mbdev.read_long(114, 3, True, minimalmodbus.BYTEORDER_LITTLE_SWAP) / 1000
            self.soc = mbdev.read_long(128, 3, False, minimalmodbus.BYTEORDER_LITTLE_SWAP) / 1000

            # self.cycles = None
            self.total_ah_drawn = None
            
            self.protection = Protection()
            
            self.charge_fet = None #OVP
            self.discharge_fet = None #LVP

            self.temp1 = mbdev.read_register(102, 0, 3, True) / 100
            self.temp2 = mbdev.read_register(103, 0, 3, True) / 100
            
            return True
        except IOError:
            return False

    # def read_cell_data(self):
    #     try:
    #         mbdevice = minimalmodbus.Instrument(self.port, self.GREENMETER_ADDRESS)  
    #         mbdevice.serial.parity = minimalmodbus.serial.PARITY_EVEN

    #         self.cells = []
    #             voltage = None
    #             temp = None
    #             balance = None

    #         return True
    #     except IOError:
    #         return False
