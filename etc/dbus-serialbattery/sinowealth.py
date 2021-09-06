# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from battery import Protection, Battery, Cell
from utils import *
from struct import *

class Sinowealth(Battery):

    def __init__(self, port,baud):
        super(Sinowealth, self).__init__(port,baud)
        self.charger_connected = None
        self.load_connected = None
        self.cell_min_voltage = None
        self.cell_max_voltage = None
        self.cell_min_no = None
        self.cell_max_no = None
        self.cell_count = None
        self.cell_voltages = {}
        self.poll_interval = 2000
        self.type = self.BATTERYTYPE
    # command bytes [StartFlag=0A][Command byte][response dataLength=2 to 20 bytes][checksum]
    command_base = b"\x0A\x00\x04"
    command_cell_base = b"\x01"
    command_total_voltage = b"\x0B"
    command_temp_ext1 = b"\x0C"
    command_temp_ext2 = b"\x0D"
    command_temp_int1 = b"\x0E"
    command_temp_int2 = b"\x0F"
    command_current = b"\x10"
    command_capacity = b"\x11"
    command_remaining_capacity = b"\x12"
    command_soc = b"\x13"
    command_cycle_count = b"\x14"
    command_status = b"\x15"
    command_battery_status = b"\x16"
    command_pack_config = b"\x17"
    
    command_cell_base = b"\x01"
    BATTERYTYPE = "Sinowealth"
    LENGTH_CHECK = 0
    LENGTH_POS = 0

    def test_connection(self):
       result = self.read_status_data()
       result = result and self.read_remaining_capacity()
       result = result and self.read_pack_config_data()
       return result

    def get_settings(self):
        # hardcoded parameters, to be requested from the BMS in the future
        self.max_battery_current = MAX_BATTERY_CURRENT
        self.max_battery_discharge_current = MAX_BATTERY_DISCHARGE_CURRENT
        
        if self.cell_count is None:
          self.read_pack_config_data()
        self.max_battery_voltage = MAX_CELL_VOLTAGE * self.cell_count
        self.min_battery_voltage = MIN_CELL_VOLTAGE * self.cell_count
        return True

    def refresh_data(self):
        result = self.read_soc()
        result = result and self.read_status_data()
        result = result and self.read_battery_status()
        result = result and self.read_pack_voltage()
        result = result and self.read_pack_current()
        result = result and self.read_cell_data()
        result = result and self.read_temperature_data()
        result = result and self.read_remaining_capacity()
        result = result and self.read_cycle_count()
        return result

    def read_status_data(self):
        status_data = self.read_serial_data_sinowealth(self.command_status)
        # check if connection success
        if status_data is False:
            return False
            
        # BMS status command layout (from screenshot)
        # [0]     -       -        -        -        -        VDQ     FD      FC
        # [1]     -       FAST_DSG MID_DSG  SLOW_DSG DSGING   CHGING  DSGMOS  CHGMOS
        self.discharge_fet = bool(status_data[1]>>1 & int(1)) # DSGMOS
        self.charge_fet = bool(status_data[1] & int(1)) # CHGMOS
        logger.info(">>> INFO: Discharge fet: %s, charge fet: %s", self.discharge_fet, self.charge_fet)
        self.charger_connected = bool(status_data[0] & int(1)) # FC
        logger.info(">>> INFO: Pack charging: %s", self.charger_connected)
        self.load_connected = bool(status_data[0]>>1 & int(1)) # FD
        logger.info(">>> INFO: Load connected: %s", self.load_connected)
        
        if self.cell_count is None:
          self.read_pack_config_data()
        self.hardware_version = "Daly/Sinowealth BMS " + str(self.cell_count) + " cells"
        logger.info(self.hardware_version)
        return True
        
    def read_battery_status(self):
        battery_status = self.read_serial_data_sinowealth(self.command_battery_status)
        # check if connection success
        if battery_status is False:
            return False
            
        # Battery status command layout (from screenshot)
        # [0]     -       CTO     AFE_SC  AFE_OV  UTD     UTC     OTD     OTC
        # [1]     -       -       -       -       OCD     OC      UV      OV
        self.protection.voltage_high = 2 if bool(battery_status[1] & int(1)) else 0 #OV
        self.protection.voltage_low = 2 if bool(battery_status[1]>>1 & int(1)) else 0 #UV
        self.protection.current_over = 2 if bool(battery_status[1]>>2 & int(1)) or bool(battery_status[1]>>3 & int(1)) else 0 # OC (OCC?)| OCD
        self.protection.temp_high_charge = 2 if bool(battery_status[0] & int(1)) else 0 # OTC
        self.protection.temp_high_discharge = 2 if bool(battery_status[0]>>1 & int(1)) else 0 # OTD
        self.protection.temp_low_charge = 2 if bool(battery_status[0]>>2 & int(1)) else 0 # UTC
        self.protection.temp_low_discharge = 2 if bool(battery_status[0]>>3 & int(1)) else 0 # UTD
        return True

    def read_soc(self):
        soc_data = self.read_serial_data_sinowealth(self.command_soc)
        # check if connection success
        if soc_data is False:
            return False
        logger.info(">>> INFO: current SOC: %u", soc_data[1])
        self.soc = soc_data[1]
        return True

    def read_cycle_count(self):
        # TODO: cyclecount does not match cycles in the app
        cycle_count = self.read_serial_data_sinowealth(self.command_cycle_count)
        # check if connection success
        if cycle_count is False:
            return False
        self.cycles = int(unpack_from('>H', cycle_count[:2])[0])
        logger.info(">>> INFO: current cycle count: %u", self.cycles)
        return True        
                
    def read_pack_voltage(self):
        pack_voltage_data = self.read_serial_data_sinowealth(self.command_total_voltage)
        if pack_voltage_data is False:
            return False
        pack_voltage = unpack_from('>H', pack_voltage_data[:-1])
        logger.info(">>> INFO: current pack voltage: %f", pack_voltage[0]/1000)
        self.voltage = pack_voltage[0]/1000
        return True

    def read_pack_current(self):
        current_data = self.read_serial_data_sinowealth(self.command_current)
        if current_data is False:
            return False
        current = unpack_from('>i', current_data[:-1])
        logger.info(">>> INFO: current pack current: %f", current[0]/1000)
        self.current = current[0]/1000
        return True
        
    def read_remaining_capacity(self):
        remaining_capacity_data = self.read_serial_data_sinowealth(self.command_remaining_capacity)
        if remaining_capacity_data is False:
            return False
        remaining_capacity = unpack_from('>i', remaining_capacity_data[:-1])
        logger.info(">>> INFO: remaining battery capacity: %f Ah", remaining_capacity[0]/1000)
        self.capacity_remain = remaining_capacity[0]/1000
        if self.capacity is None:
          self.read_capacity()
        self.total_ah_drawn = self.capacity - self.capacity_remain
        return True
 
    def read_capacity(self):
        capacity_data = self.read_serial_data_sinowealth(self.command_capacity)
        if capacity_data is False:
            return False
        capacity = unpack_from('>i', capacity_data[:-1])
        logger.info(">>> INFO: Battery capacity: %f Ah", capacity[0]/1000)
        self.capacity = capacity[0]/1000
        return True       
        
    def read_pack_config_data(self):
        # TODO: detect correct chipset, currently the pack_config_map register is parsed as,
        # SH367303 / 367305 / 367306 / 39F003 / 39F004 / BMS_10. So these are the currently supported chips
        pack_config_data = self.read_serial_data_sinowealth(self.command_pack_config)
        if pack_config_data is False:
            return False
        cell_cnt_mask = int(7)
        self.cell_count = (pack_config_data[1] & cell_cnt_mask) + 3
        logger.info(">>> INFO: Number of cells: %u", self.cell_count)
        temp_sens_mask = int(~(1 << 6))
        self.temp_sensors = 1 if (pack_config_data[1] & temp_sens_mask) else 2 # one means two
        logger.info(">>> INFO: Number of temperatur sensors: %u", self.temp_sensors)
        return True
        
    def read_cell_data(self):
        if self.cell_count is None:
          self.read_pack_config_data()
          
        cell_index = 1
        while cell_index <= self.cell_count:
          self.cell_voltages[cell_index] = self.read_cell_voltage(cell_index)
          if self.cell_voltages[cell_index] is False:
            return False
          cell_index += 1
        
        self.cell_max_no = max(self.cell_voltages, key=int) - 1
        self.cell_max_voltage = max(self.cell_voltages.values())
        self.cell_min_no = min(self.cell_voltages, key=int) - 1
        self.cell_min_voltage = min(self.cell_voltages.values())
        
        logger.info(">>> INFO: Max cell voltage: %u:%f", self.cell_max_no, self.cell_max_voltage)
        logger.info(">>> INFO: Min cell voltage: %u:%f", self.cell_min_no, self.cell_min_voltage)
        
        self.max_battery_voltage = 3.65 * self.cell_count
        self.min_battery_voltage = 2.5 * self.cell_count
        return True
        
    def read_cell_voltage(self, cell_index):
        cell_data = self.read_serial_data_sinowealth(str(chr(cell_index)))
        if cell_data is False:
            return False
        cell_voltage = unpack_from('>H', cell_data[:-1])
        logger.info(">>> INFO: Cell %u voltage: %f V", cell_index, cell_voltage[0]/1000 )
        
        return cell_voltage[0]/1000

    def read_temperature_data(self):
        if self.temp_sensors is None:
            self.read_pack_config_data()
        temp_ext1_data = self.read_serial_data_sinowealth(self.command_temp_ext1)
        if temp_ext1_data is False:
            return False
        kelvin = 273.1
        temp_ext1 = unpack_from('>H', temp_ext1_data[:-1])
        logger.info(">>> INFO: BMS external temperature 1: %f C", temp_ext1[0]/10 - kelvin )

        self.temp1 = temp_ext1[0]/100
        
        if self.temp_sensors is 2:
            temp_ext2_data = self.read_serial_data_sinowealth(self.command_temp_ext2)
            if temp_ext2_data is False:
                return False
            
            temp_ext2 = unpack_from('>H', temp_ext2_data[:-1])
            logger.info(">>> INFO: BMS external temperature 2: %f C", temp_ext2[0]/10 - kelvin )

            self.temp2 = temp_ext2[0]/100
        
        # Internal temperature 1 seems to give a logical value 
        temp_int1_data = self.read_serial_data_sinowealth(self.command_temp_int1)
        if temp_int1_data is False:
            return False
            
        temp_int1 = unpack_from('>H', temp_int1_data[:-1])
        logger.info(">>> INFO: BMS internal temperature 1: %f C", temp_int1[0]/10 - kelvin )
        
        # Internal temperature 2 seems to give a useless value 
        temp_int2_data = self.read_serial_data_sinowealth(self.command_temp_int2)
        if temp_int2_data is False:
            return False
            
        temp_int2 = unpack_from('>H', temp_int2_data[:-1])
        logger.info(">>> INFO: BMS internal temperature 2: %f C", temp_int2[0]/10 - kelvin )
        return True

    def generate_command(self, command):
        buffer = bytearray(self.command_base)
        buffer[1] = command
        return buffer

    def read_serial_data_sinowealth(self, command):
        data = read_serial_data(self.generate_command(command), self.port, self.baud_rate, self.LENGTH_POS, self.LENGTH_CHECK, int(self.generate_command(command)[2]))
        if data is False:
            return False

        return bytearray(data)
