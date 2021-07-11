# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from battery import Protection, Battery, Cell
from struct import *
from utilis_max17853 import *

class MNB_Protection(Protection):

    def __init__(self):
        super(MNB_Protection, self).__init__()
        self.voltage_high_cell = False
        self.voltage_low_cell = False
        self.short = False
        self.IC_inspection = False
        self.software_lock = False

    def set_voltage_high_cell(self, value):
        self.voltage_high_cell = value
        self.set_cell_imbalance(2 if self.voltage_low_cell \
                                        or self.voltage_high_cell else 0)

    def set_voltage_low_cell(self, value):
        self.voltage_low_cell = value
        self.set_cell_imbalance(2 if self.voltage_low_cell \
                                        or self.voltage_high_cell else 0)

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

class MNB(Battery):

    def __init__(self, port,baud,address=0):
        super(MNB, self).__init__(port,baud)
        self.hardware_version = 1.02
        self.voltage = 26
        self.charger_connected = None
        self.load_connected = None
        self.command_address = address
        self.cell_min_voltage = None
        self.cell_max_voltage = None
        self.cell_min_no = None
        self.cell_max_no = None
        self.poll_interval = 2000
        self.type = self.BATTERYTYPE
        self.capacity = None
        self.capacity_remain = None
        self.current = None
        self.temp3 = None
        self.temp4 = None
        self.cells_v= [3.3,3.31,3.33,3.34,3.35,3.36,3.37]
        self.cells_b=[0,0,0,0,0,0,0,0]
        
    BATTERYTYPE = "MNB-Li" 

    def test_connection(self):
        init_max()
        return self.read_status_data()

    def get_settings(self):  # imutable constants for the battery
        # Need to include this in BMS initialisation
        # Thresholds need to be set also, or derived from 
        # cell voltage values. Other BMS user parameters
        # also need to be defined here so all settings are in one place.
        #*****************************************************************
        self.max_battery_current = 200 #MAX_BATTERY_CURRENT
        self.max_battery_discharge_current = 200 #MAX_BATTERY_DISCHARGE_CURRENT
        self.V_C_min = 2.55
        self.V_C_max = 3.65
        self.cell_count =8
        self.capacity = 36*3.6
        self.version = "V1.02"
        self.temp_sensors =6
        #self.T_Cells = [25]*self.temp_sensors
        self.max_battery_voltage = self.V_C_max * self.cell_count
        self.min_battery_voltage = self.V_C_min * self.cell_count
        self.hardware_version = "MNB_BMS " + str(self.cell_count) + " cells"
        return True

    def refresh_data(self):
        # Run acquisition cycle.
        result = data_cycle(self)
        return result

    def read_status_data(self):
        # used once in init...
        self.charger_connected = True
        self.load_connected = True
        self.state = True  
        self.cycles = 200
        
        return True
#************************************************************************
# Following routines are not used, as all work is done in data_cycle()
# These can exist, just commented out for development.
#************************************************************************

    # def read_soc_data(self):
        
    #     # voltage, tmp, current, soc = unpack_from('>hhhh', soc_data)
    #     self.voltage = 26.7
    #     self.current = 15.3
    #     self.soc = 65.0
    #     self.capacity_remain = self.soc*self.capacity #soc * capacity?
    #     return True

    # def read_cell_voltage_range_data(self):
        

    #     self.cell_max_voltage = 3.39
    #     self.cell_max_no=6
    #     self.cell_min_voltage = 3.18
    #     self.cell_min_no = 2
        
    #     return True

    # def read_temperature_range_data(self):
        
    #     max_temp = 0
    #     min_temp = 45
    #     for index,t in enumerate(self.T_cells):
    #         if t > max_temp:
    #             max_temp = t 
    #         if t < min_temp:
    #             min_temp = t
    #     self.temp1 = min_temp 
    #     self.temp2 = max_temp 
    #     return True

    # def read_fed_data(self):
        
    #     # Relay status
    #     status = True
    #     self.charge_fet = True
    #     self.discharge_fet = True 
    #     bms_cycles =15
    #     return True

    def manage_charge_current(self):
        # Start with the current values

        # Change depending on the cell_max_voltage values

        if self.cell_max_voltage > self.V_C_max-.05:
            self.control_allow_charge = False
        else:
            self.control_allow_charge = True
        # Change depending on the cell_max_voltage values
        if self.cell_max_voltage > self.V_C_max-0.15:
            b= 10*(self.V_C_max - self.cell_max_voltage-.05)
            if b >1:
                b=1 
            if b <0:
                b = 0
            self.control_charge_current = self.max_battery_current *b
        
        else:
            self.control_charge_current = self.max_battery_current

        # Change depending on the cell_min_voltage values
        if self.cell_min_voltage < self.V_C_min+0.05:
           self.control_allow_dicharge = False
        else:
           self.control_allow_dicharge = True
           
        if self.cell_min_voltage < self.V_C_min+0.15:
            b = 10*(self.cell_min_voltage - self.V_C_min-.05)
            if b > 1:
                b=1
            if b < 0:
                b = 0
            self.control_discharge_current = self.max_battery_discharge_current*b
        else:
            self.control_discharge_current = self.max_battery_discharge_current   

    def get_balancing(self):
        for c in range(self.cell_count):
            if self.cells_b[c] is not None and self.cells_b[c]:
                return True
        return False
