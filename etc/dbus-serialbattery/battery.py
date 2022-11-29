# -*- coding: utf-8 -*-
from utils import *
import math
from datetime import timedelta
from time import time

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
    temp = None

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
        self.allow_max_voltage = True
        self.max_voltage_start_time = None
        self.control_current = None
        self.control_previous_total = None
        self.control_previous_max = None
        self.control_discharge_current = None
        self.control_charge_current = None
        self.control_allow_charge = None
        self.control_allow_discharge = None
        # max battery charge/discharge current
        self.max_battery_charge_current = None
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
        #   MAX_BATTERY_CHARGE_CURRENT, MAX_BATTERY_DISCHARGE_CURRENT, cell_count, capacity
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

    def manage_charge_voltage(self):
        if LIMITATION_MODE == "WaldemarFech":
            return self.manage_charge_voltage_waldemar_fech()
        elif LIMITATION_MODE == "Classic":
            return self.manage_charge_voltage_classic()

    def manage_charge_voltage_waldemar_fech(self):
        if CVCM_ENABLE:
            foundHighCellVoltage = False
            currentBatteryVoltage = 0
            penaltySum = 0
            for i in range(self.cell_count):
                cv = self.cells[i].voltage
                if cv:
                    currentBatteryVoltage += cv

                    if cv >= PENALTY_AT_CELL_VOLTAGE[0]:
                        foundHighCellVoltage = True
                        penaltySum += calcLinearRelationship(cv, PENALTY_AT_CELL_VOLTAGE, PENALTY_BATTERY_VOLTAGE)

            self.voltage = currentBatteryVoltage    # for testing
            if foundHighCellVoltage:
                self.control_voltage = currentBatteryVoltage - penaltySum
            else:
                self.control_voltage = MAX_CELL_VOLTAGE * self.cell_count
            return penaltySum

    def manage_charge_voltage_classic(self):
        voltageSum = 0
        if (CVCM_ENABLE):
            for i in range(self.cell_count):
                voltage = self.cells[i].voltage
                if voltage:
                    voltageSum+=voltage

            if None == self.max_voltage_start_time:
                if MAX_CELL_VOLTAGE * self.cell_count <= voltageSum and True == self.allow_max_voltage:
                    self.max_voltage_start_time = time()
                else:
                    if SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT > self.soc and not self.allow_max_voltage:
                        self.allow_max_voltage = True
            else:
                tDiff = time() - self.max_voltage_start_time
                if MAX_VOLTAGE_TIME_SEC < tDiff:
                    self.max_voltage_start_time = None
                    self.allow_max_voltage = False

        if self.allow_max_voltage:
            self.control_voltage = MAX_CELL_VOLTAGE * self.cell_count
        else:
            self.control_voltage = FLOAT_CELL_VOLTAGE * self.cell_count

    def manage_charge_current(self):
        if LIMITATION_MODE == "WaldemarFech":
            return self.manage_current_waldemar_fech()
        elif LIMITATION_MODE == "Classic":
            return self.manage_charge_current_classic()

    def manage_current_waldemar_fech(self):
        # Manage Charge Current Limitations
        if CCCM_CV_ENABLE:
            currentLimit_CV = self.calcMaxChargeCurrentReferringToCellVoltage()
        else:
            currentLimit_CV = self.max_battery_charge_current

        if CCCM_T_ENABLE:
            currentLimit_T = self.calcMaxChargeCurrentReferringToTemperature()
        else:
            currentLimit_T = self.max_battery_charge_current

        self.control_charge_current = min(currentLimit_CV, currentLimit_T)

        if self.control_charge_current == 0:
            self.control_allow_charge = False
        else:
            self.control_allow_charge = True



        # Manage Discharge Current Limitations
        if DCCM_CV_ENABLE:
            currentLimit_CV = self.calcMaxDischargeCurrentReferringToCellVoltage()
        else:
            currentLimit_CV = self.max_battery_discharge_current

        if DCCM_T_ENABLE:
            currentLimit_T = self.calcMaxDischargeCurrentReferringToTemperature()
        else:
            currentLimit_T = self.max_battery_discharge_current

        self.control_discharge_current = min(currentLimit_CV, currentLimit_T)

        if self.control_discharge_current == 0:
            self.control_allow_discharge = False
        else:
            self.control_allow_discharge = True

    def calcMaxChargeCurrentReferringToCellVoltage(self):
        return calcLinearRelationship(self.get_max_cell_voltage(),
                                      CELL_VOLTAGES_WHILE_CHARGING, MAX_CHARGE_CURRENT_CV)

    def calcMaxDischargeCurrentReferringToCellVoltage(self):
        return calcLinearRelationship(self.get_min_cell_voltage(),
                                      CELL_VOLTAGES_WHILE_DISCHARGING, MAX_DISCHARGE_CURRENT_CV)

    def calcMaxChargeCurrentReferringToTemperature(self):
        if self.get_max_temp() is None:
            return self.max_battery_charge_current

        temps = {0: self.get_max_temp(), 1: self.get_min_temp()}

        for key, currentMaxTemperature in temps.items():
            temps[key] = calcLinearRelationship(currentMaxTemperature,
                                                TEMPERATURE_LIMITS_WHILE_CHARGING, MAX_CHARGE_CURRENT_T)

        return min(temps[0], temps[1])

    def calcMaxDischargeCurrentReferringToTemperature(self):
        if self.get_max_temp() is None:
            return self.max_battery_discharge_current

        temps = {0: self.get_max_temp(), 1: self.get_min_temp()}

        for key, currentMaxTemperature in temps.items():
            temps[key] = calcLinearRelationship(currentMaxTemperature,
                                                TEMPERATURE_LIMITS_WHILE_DISCHARGING, MAX_DISCHARGE_CURRENT_T)

        return min(temps[0], temps[1])

    def manage_charge_current_classic(self):
        # If disabled make sure the default values are set and then exit
        if (not CCCM_ENABLE):
            self.control_charge_current = self.max_battery_charge_current
            self.control_allow_charge = True
        else:
            # Start with the current values
            # Charge depending on the SOC values
            if not (self.soc is None):
                if self.soc > 99:
                    self.control_allow_charge = False
                else:
                    self.control_allow_charge = True
                # Charge depending on the SOC values
                if CC_SOC_LIMIT1 < self.soc <= 100:  # CC_SOC_LIMIT1 = 98
                    self.control_charge_current = CC_CURRENT_LIMIT1  # CC_CURRENT_LIMIT1 = 5
                elif CC_SOC_LIMIT2 < self.soc <= CC_SOC_LIMIT1:  # CC_SOC_LIMIT2 = 95
                    self.control_charge_current = CC_CURRENT_LIMIT2 # CC_CURRENT_LIMIT2 = MAX_BATTERY_CHARGE_CURRENT/4
                elif CC_SOC_LIMIT3 < self.soc <= CC_SOC_LIMIT2:  # CC_SOC_LIMIT3 = 91
                    self.control_charge_current = CC_CURRENT_LIMIT3  # CC_CURRENT_LIMIT3 = MAX_BATTERY_CHARGE_CURRENT/2
                else:
                    self.control_charge_current = self.max_battery_charge_current

        if (not DCCM_ENABLE):
            self.control_discharge_current = self.max_battery_discharge_current
            self.control_allow_discharge = True
        else:
            if not (self.soc is None):
                if self.soc < 1:
                    self.control_allow_discharge = False
                else:
                    self.control_allow_discharge = True
                # Discharge depending on the SOC values
                if self.soc <= DC_SOC_LIMIT1: #DC_SOC_LIMIT1 = 10
                    self.control_discharge_current = DC_CURRENT_LIMIT1  #DC_CURRENT_LIMIT1 = 5
                elif DC_SOC_LIMIT1 < self.soc <= DC_SOC_LIMIT2:  #DC_SOC_LIMIT2 = 20
                    self.control_discharge_current = DC_CURRENT_LIMIT2 #DC_CURRENT_LIMIT2 = max_discharge/4
                elif DC_SOC_LIMIT2 < self.soc <= DC_SOC_LIMIT3: #DC_SOC_LIMIT3 = 30
                    self.control_discharge_current = DC_CURRENT_LIMIT3 #DC_CURRENT_LIMIT3 = max_discharge/2
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

    def get_capacity_remain(self):
        if self.capacity_remain is not None:
            return self.capacity_remain
        if self.capacity is not None and self.soc is not None:
            return self.capacity * self.soc / 100
        return None

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
        if hasattr(self, 'cell_min_voltage'):
            min_voltage = self.cell_min_voltage

        if min_voltage is None:
            try:
                min_voltage = min(c.voltage for c in self.cells if c.voltage is not None)
            except ValueError:
                pass
        return min_voltage

    def get_max_cell_voltage(self):
        max_voltage = None
        if hasattr(self, 'cell_max_voltage'):
            max_voltage = self.cell_max_voltage

        if max_voltage is None:
            try:
                max_voltage = max(c.voltage for c in self.cells if c.voltage is not None)
            except ValueError:
                pass
        return max_voltage

    def get_midvoltage(self):
        if not MIDPOINT_ENABLE or self.cell_count is None or self.cell_count == 0 or self.cell_count < 4 or len(self.cells) != self.cell_count:
            return None, None

        halfcount = int(math.floor(self.cell_count/2))
        half1voltage = 0
        half2voltage = 0

        try:
            half1voltage = sum(c.voltage for c in self.cells[:halfcount] if c.voltage is not None)
            half2voltage = sum(c.voltage for c in self.cells[halfcount:halfcount*2] if c.voltage is not None)
        except ValueError:
            pass

        try:
            # handle uneven cells by giving half the voltage of the last cell to half1 and half2
            extra = 0 if (2*halfcount == self.cell_count) else self.cells[self.cell_count-1].voltage/2
            # get the midpoint of the battery
            midpoint = (half1voltage + half2voltage)/2 + extra
            return midpoint, (half2voltage-half1voltage)/(half2voltage+half1voltage)*100
        except ValueError:
            return None, None

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
        logger.debug("Cells:" + cell_res)
        return True

    def log_settings(self):

        logger.info(f'Battery connected to dbus from {self.port}')
        logger.info(f'=== Settings ===')
        cell_counter = len(self.cells)
        logger.info(f'> Connection voltage {self.voltage}V | current {self.current}A | SOC {self.soc}%')
        logger.info(f'> Cell count {self.cell_count} | cells populated {cell_counter}')
        logger.info(f'> CCL Charge {self.max_battery_charge_current}A | DCL Discharge {self.max_battery_discharge_current}A')
        logger.info(f'> MIN_CELL_VOLTAGE {MIN_CELL_VOLTAGE}V | MAX_CELL_VOLTAGE {MAX_CELL_VOLTAGE}V')

        return