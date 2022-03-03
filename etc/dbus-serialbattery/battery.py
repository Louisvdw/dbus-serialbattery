# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from utils import *
import math
from datetime import timedelta

class Protection(object):
    # 2 = Alarm, 1 = Warning, 0 = Normal
    def __init__(self):
        self.voltage_high = None
        self.voltage_low = None
        self.voltage_cell_low = None
        self.soc_low = None
        self.current_over = None
        self.current_under = None
        self.cell_imbalance = None
        self.internal_failure = None
        self.temp_high_charge = None
        self.temp_low_charge = None
        self.temp_high_discharge = None
        self.temp_low_discharge = None


class Cell:
    voltage = None
    balance = None

    def __init__(self, balance):
        self.balance = balance


class Battery(object):

    def __init__(self, port, baud):
        self.port = port
        self.baud_rate = baud
        self.role = 'battery'
        self.type = 'Generic'
        self.poll_interval = 1000
        self.online = True

        self.hardware_version = None
        self.voltage = None
        self.current = None
        self.capacity_remain = None
        self.capacity = None
        self.cycles = None
        self.total_ah_drawn = None
        self.production = None
        self.protection = Protection()
        self.version = None
        self.soc = None
        self.charge_fet = None
        self.discharge_fet = None
        self.cell_count = None
        self.temp_sensors = None
        self.temp1 = None
        self.temp2 = None
        self.cells = []
        self.control_charging = None
        self.control_voltage = None
        self.control_current = None
        self.control_previous_total = None
        self.control_previous_max = None
        self.control_discharge_current = None
        self.control_charge_current = None
        self.control_allow_charge = None
        # max battery charge/discharge current
        self.max_battery_current = None
        self.max_battery_discharge_current = None
        
        self.time_to_soc_update = TIME_TO_SOC_LOOP_CYCLES

    def test_connection(self):
        # Each driver must override this function to test if a connection can be made
        # return false when fail, true if successful
        return False

    def get_settings(self):
        # Each driver must override this function to read/set the battery settings
        # It is called once after a successful connection by DbusHelper.setup_vedbus()
        # Values:  battery_type, version, hardware_version, min_battery_voltage, max_battery_voltage,
        #   MAX_BATTERY_CURRENT, MAX_BATTERY_DISCHARGE_CURRENT, cell_count, capacity
        # return false when fail, true if successful
        return False

    def refresh_data(self):
        # Each driver must override this function to read battery data and populate this class
        # It is called each poll just before the data is published to vedbus
        # return false when fail, true if successful
        return False

    def to_temp(self, sensor, value):
        # Keep the temp value between -20 and 100 to handle sensor issues or no data.
        # The BMS should have already protected before those limits have been reached.
        if sensor == 1:
            self.temp1 = min(max(value, -20), 100)
        if sensor == 2:
            self.temp2 = min(max(value, -20), 100)

    def manage_charge_current(self):
        # Start with the current values

        # Change depending on the SOC values
        if self.soc is None:
            # Prevent serialbattery from terminating on error
            return False
            
        if self.soc > 99:
            self.control_allow_charge = False
        else:
            self.control_allow_charge = True
        # Change depending on the SOC values
        if 98 < self.soc <= 100:
            self.control_charge_current = 5
        elif 95 < self.soc <= 98:
            self.control_charge_current = self.max_battery_current/4
        elif 91 < self.soc <= 95:
            self.control_charge_current = self.max_battery_current/2
        else:
            self.control_charge_current = self.max_battery_current

        # Change depending on the SOC values
        if self.soc <= 10:
            self.control_discharge_current = 5
        elif 10 < self.soc <= 20:
            self.control_discharge_current = self.max_battery_discharge_current/4
        elif 20 < self.soc <= 30:
            self.control_discharge_current = self.max_battery_discharge_current/2
        else:
            self.control_discharge_current = self.max_battery_discharge_current

    def get_min_cell(self):
        min_voltage = 9999
        min_cell = None
        if len(self.cells) == 0 and hasattr(self, 'cell_min_no'):
            return self.cell_min_no

        for c in range(min(len(self.cells), self.cell_count)):
            if self.cells[c].voltage is not None and min_voltage > self.cells[c].voltage:
                min_voltage = self.cells[c].voltage
                min_cell = c
        return min_cell

    def get_max_cell(self):
        max_voltage = 0
        max_cell = None
        if len(self.cells) == 0 and hasattr(self, 'cell_max_no'):
            return self.cell_max_no

        for c in range(min(len(self.cells), self.cell_count)):
            if self.cells[c].voltage is not None and max_voltage < self.cells[c].voltage:
                max_voltage = self.cells[c].voltage
                max_cell = c
        return max_cell

    def get_min_cell_desc(self):
        cell_no = self.get_min_cell()
        return cell_no if cell_no is None else 'C' + str(cell_no + 1)

    def get_max_cell_desc(self):
        cell_no = self.get_max_cell()
        return cell_no if cell_no is None else 'C' + str(cell_no + 1)

#cell voltages - begining
    def get_cell_voltage(self, idx):
        if idx>=min(len(self.cells), self.cell_count):
          return None
        return self.cells[idx].voltage
 
    def get_cell_balancing(self, idx):
        if idx>=min(len(self.cells), self.cell_count):
          return None
        if self.cells[idx].balance is not None and self.cells[idx].balance:
          return 1
        return 0


    def get_timetosoc(self, socnum, crntPrctPerSec):
        if self.current > 0:
            diffSoc = (socnum - self.soc)
        else:
            diffSoc = (self.soc - socnum)

        ttgStr = None
        if self.soc != socnum and (diffSoc > 0 or TIME_TO_SOC_INC_FROM is True):
            secondstogo = int(diffSoc / crntPrctPerSec)
            ttgStr = ""

            if (TIME_TO_SOC_VALUE_TYPE & 1):
                ttgStr += str(secondstogo)
                if (TIME_TO_SOC_VALUE_TYPE & 2):
                    ttgStr += " ["
            if (TIME_TO_SOC_VALUE_TYPE & 2):
                ttgStr += str(timedelta(seconds=secondstogo))
                if (TIME_TO_SOC_VALUE_TYPE & 1):
                    ttgStr += "]"
                    
        return ttgStr

    
    def get_min_cell_voltage(self):
        min_voltage = None
        if len(self.cells) == 0 and hasattr(self, 'cell_min_voltage'):
            return self.cell_min_voltage

        try:
            min_voltage = min(c.voltage for c in self.cells if c.voltage is not None)
        except ValueError:
            pass
        return min_voltage

    def get_max_cell_voltage(self):
        max_voltage = None
        if len(self.cells) == 0 and hasattr(self, 'cell_max_voltage'):
            return self.cell_max_voltage

        try:
            max_voltage = max(c.voltage for c in self.cells if c.voltage is not None)
        except ValueError:
            pass
        return max_voltage

    def get_midvoltage(self):
        if self.cell_count is None or self.cell_count == 0 or self.cell_count < 4 or len(self.cells) != self.cell_count:
            return None, None

        halfcount = int(math.floor(self.cell_count/2))
        half1voltage = 0
        half2voltage = 0
        
        try:
            half1voltage = sum(c.voltage for c in self.cells[:halfcount] if c.voltage is not None)
            half2voltage = sum(c.voltage for c in self.cells[halfcount:halfcount*2] if c.voltage is not None)
        except ValueError:
            pass
        # handle uneven cells by giving half the voltage of the last cell to half1 and half2
        extra = 0 if (2*halfcount == self.cell_count) else self.cells[self.cell_count-1].voltage/2
        # get the midpoint of the battery
        midpoint = (half1voltage + half2voltage)/2 + extra   
        return midpoint, abs(1 - half1voltage/half2voltage)*100

    def get_balancing(self):
        for c in range(min(len(self.cells), self.cell_count)):
            if self.cells[c].balance is not None and self.cells[c].balance:
                return 1
        return 0

    def get_temp(self):
        if self.temp1 is not None and self.temp2 is not None:
            return round((float(self.temp1) + float(self.temp2)) / 2, 2)
        if self.temp1 is not None and self.temp2 is None:
            return round(float(self.temp1) , 2)
        if self.temp1 is None and self.temp2 is not None:
            return round(float(self.temp2) , 2)
        else:
            return None

    def get_min_temp(self):
        if self.temp1 is not None and self.temp2 is not None:
            return min(self.temp1, self.temp2)
        if self.temp1 is not None and self.temp2 is None:
            return self.temp1
        if self.temp1 is None and self.temp2 is not None:
            return self.temp2
        else:
            return None

    def get_max_temp(self):
        if self.temp1 is not None and self.temp2 is not None:
            return max(self.temp1, self.temp2)
        if self.temp1 is not None and self.temp2 is None:
            return self.temp1
        if self.temp1 is None and self.temp2 is not None:
            return self.temp2
        else:
            return None

    def log_cell_data(self):
        if logger.getEffectiveLevel() > logging.INFO and len(self.cells) == 0:
            return False

        cell_res = ""
        cell_counter = 1
        for c in self.cells:
            cell_res += "[{0}]{1}V ".format(cell_counter, c.voltage)
            cell_counter = cell_counter + 1
        logger.info("Cells:" + cell_res)
        return True
