# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from battery import Protection, Battery, Cell
from struct import *
#from test_max17853 import *#{these two lines are mutually}
from util_max17853 import * #{exclusive. use test for testing}

class MNBProtection(Protection):

    def __init__(self):
        super(MNBProtection, self).__init__()
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
        self.protection = MNBProtection()
        self.hardware_version = 1.02
        self.voltage = 26
        self.charger_connected = None
        self.load_connected = None
        self.command_address = address
        self.cell_min_voltage = 3.3
        self.cell_max_voltage = 3.3
        self.soc = 50
        self.cell_min_no = None
        self.cell_max_no = None
        self.temp_sensors = None
        self.temp_max_no = None
        self.temp_min_no = None
        self.T_C_max = None
        self.T_C_min = None
        self.poll_interval = None
        self.type = self.BATTERYTYPE
        self.inst_capacity = None
        self.max_battery_current = None
        self.max_battery_discharge_current = None
        self.V_C_min = None
        self.V_C_max = None
        self.max_battery_voltage = None
        self.min_battery_voltage = None
        self.capacity = None
        self.C_rating = None
        self.current = None
        self.temp3 = None
        self.temp4 = None
        self.cells= []
        #self.cells_b=[]
        
    BATTERYTYPE = "MNB-Li SPI" 
    
    def test_connection(self):
        self.get_settings()
        init_max(self)
        return self.read_status_data()

    def get_settings(self):  # imutable constants for the battery
        # Need to include this in BMS initialisation
        # Thresholds need to be set also, or derived from 
        # cell voltage values. Other BMS user parameters
        # also need to be defined here so all settings are in one place.
        #*****************************************************************
        self.inst_capacity = 36*3.6 # Equivalent cell capacity Ah
        self.C_rating = 1      # Max current/Ah eg 1, 0.5 or 0.25
        self.max_battery_current = self.inst_capacity*self.C_rating #MAX_BATTERY_CURRENT = Crating * Capacity
        self.max_battery_discharge_current = self.inst_capacity*self.C_rating #MAX_BATTERY_DISCHARGE_CURRENT
        self.V_C_min = 2.55     # Min cell voltage permitted
        self.V_C_max = 3.65     # Max cell voltage permitted
        self.cell_count = 8      # Number of cells in series (max) 8 for 24V
        self.version = "V2.01"
        self.temp_sensors =6
        self.T_C_max = 40
        self.T_C_min = 15
        self.max_battery_voltage = self.V_C_max * self.cell_count
        self.min_battery_voltage = self.V_C_min * self.cell_count
        self.hardware_version = "MNB_BMS " + str(self.cell_count) + " cells"
        self.poll_interval = 1000 #scan repeat time, ms
        for c in range(self.cell_count):
            self.cells.append(Cell(False))
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
        self.cycles = None
        
        return True


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
