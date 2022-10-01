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
    GREENMETER_ID_500A = 500
    GREENMETER_ID_250A = 501
    GREENMETER_ID_125A = 502
    METER_SIZE = ""
    
    def test_connection(self):
        # call a function that will connect to the battery, send a command and retrieve the result.
        # The result or call should be unique to this BMS. Battery name or version, etc.
        # Return True if success, False for failure
        
        # Trying to find Green Meter ID
        try:
            mbdev = minimalmodbus.Instrument(self.port, GREENMETER_ADDRESS)  
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
        self.cell_count = LIPRO_CELL_COUNT
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
            mbdev = minimalmodbus.Instrument(self.port, GREENMETER_ADDRESS)  
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
            mbdev = minimalmodbus.Instrument(self.port, GREENMETER_ADDRESS)  
            mbdev.serial.parity = minimalmodbus.serial.PARITY_EVEN

            self.voltage = mbdev.read_long(108, 3, False, minimalmodbus.BYTEORDER_LITTLE_SWAP) / 1000
            self.current = mbdev.read_long(114, 3, True, minimalmodbus.BYTEORDER_LITTLE_SWAP) / 1000
            # if (mbdev.read_register(129, 0, 3, False) != 65535):
            temp_soc = mbdev.read_long(128, 3, False, minimalmodbus.BYTEORDER_LITTLE_SWAP) 
            # Fix for Greenmeter that seems to not correctly define/set the high bytes 
            # if the SOC value is less than 65535 (65.535%). So 50% comes through as #C350 FFFF instead of #C350 0000
            self.soc = (temp_soc if temp_soc < 4294901760 else temp_soc-4294901760) / 1000

            # self.cycles = None
            self.total_ah_drawn = None
            
            self.protection = Protection()
            
            over_voltage = mbdev.read_register(130, 0, 3, True)
            under_voltage = mbdev.read_register(131, 0, 3, True)
            self.charge_fet = True if over_voltage == 0 else False
            self.discharge_fet = True if under_voltage == 0 else False
            self.protection.voltage_high = 2 if over_voltage == 1 else 0
            self.protection.voltage_low = 2 if under_voltage == 1 else 0
            self.protection.temp_high_charge = 1 if over_voltage in range(3,5) else 0
            self.protection.temp_low_charge = 1 if over_voltage in range(5,7) else 0
            self.protection.temp_high_discharge = 1 if under_voltage in range(3,5) else 0
            self.protection.temp_low_discharge = 1 if under_voltage in range(5,7) else 0
            self.protection.current_over = 1 if over_voltage == 2 else 0
            self.protection.current_under = 1 if under_voltage == 2 else 0


            self.temp1 = mbdev.read_register(102, 0, 3, True) / 100
            self.temp2 = mbdev.read_register(103, 0, 3, True) / 100
            
            return True
        except IOError:
            return False

    # def read_cell_data(self):
    #     try:
    #         mbdevice = minimalmodbus.Instrument(self.port, GREENMETER_ADDRESS)  
    #         mbdevice.serial.parity = minimalmodbus.serial.PARITY_EVEN

    #         self.cells = []
    #             voltage = None
    #             temp = None
    #             balance = None

    #         return True
    #     except IOError:
    #         return False
