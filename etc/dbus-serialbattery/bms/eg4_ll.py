# -*- coding: utf-8 -*-

# Notes
# Added by https://github.com/tuxntoast

from battery import Battery, Cell

# from batters import Protection
from utils import logger, read_serial_data
from struct import unpack_from
import utils
import sys

#    Author: Pfitz /
#    Date: 28 Mar 2024
#    Version 1.0
#     Cell Voltage Implemented
#     Hardware Name / Version / Serial Implemented
#     Error / Warn / Protection Implemented
#     SoH / SoC State Implemented
#     Temp Implemented
#     Battery Voltage / Current
#     BMS Config Read (Limited Values right now)

#     Tasks:
#       - When starting via start-serial, the connection reports a not successful
#         Yet, tailing the serial log it is clear the driver is loaded, and working
#         as it should. Has been stable for me.
#       - Balacing Logic was buggy, commented out, and need to look more into
#       - Multi-Battery Support - Has not been tested. Hardware ID is collected and used
#         so using one usb to rx per bms should work.


# Battery Tested on:
# Eg4 LL 12v 400 AH (single battery)
# battery should be set to ID = 1 via the DIP switches

# BMS Documentation Sourced:
# https://eg4electronics.com/wp-content/uploads/2022/09/egll-MODBUS-Communication-Protocol_ENG-correct-1.pdf


class EG4_LL(Battery):
    def __init__(self, port, baud, address):

        super(EG4_LL, self).__init__(port, baud, address)
        self.charger_connected = None
        self.load_connected = None
        self.command_address = address
        self.cell_min_voltage = None
        self.cell_max_voltage = None
        self.cell_min_no = None
        self.cell_max_no = None
        self.poll_interval = 2000
        self.type = self.BATTERYTYPE
        self.has_settings = 1
        self.reset_soc = 0
        self.soc_to_set = None
        self.runtime = 0  # TROUBLESHOOTING for no reply errors
        self.trigger_force_disable_discharge = None
        self.trigger_force_disable_charge = None

    # Modbus uses 7C call vs Lifepower 7E, as return values do not correlate to the Lifepower ones if 7E is used.
    # at least on my own BMS.
    debug = False  # Set to true for wordy debugging in logs
    debug_hex = False
    debug_config_hex = False
    debug_config = False
    balancing = 0
    BATTERYTYPE = "EG4 LL"
    LENGTH_CHECK = 0
    LENGTH_POS = 2  # offset starting from 0
    LENGTH_FIXED = -1

    command_get_version = b"\x01\x03\x00\x69\x00\x23\xD4\x0F"  # Pulled from PC Client
    command_get_stats = b"\x01\x03\x00\x00\x00\x27\x05\xD0"  # Pulled from PC Client
    command_get_config = b"\x01\x03\x00\x2D\x00\x5B\x94\x38"  # Pulled from PC Client

    def unique_identifier(self) -> str:
        return self.serial_number

    def test_connection(self):
        # call a function that will connect to the battery, send a command and retrieve the result.
        # The result or call should be unique to this BMS. Battery name or version, etc.
        # Return True if success, False for failure
        result = False
        try:
            result = self.read_gen_data()
            result = result and self.get_settings()
        except Exception:
            (
                exception_type,
                exception_object,
                exception_traceback,
            ) = sys.exc_info()
            file = exception_traceback.tb_frame.f_code.co_filename
            line = exception_traceback.tb_lineno
            logger.error(
                f"Exception occurred: {repr(exception_object)} of type {exception_type} in {file} line #{line}"
            )
            result = False

        return result

    def get_settings(self):
        # After successful  connection get_settings will be call to set up the battery.
        # Return True if success, False for failure
        status_results = self.read_cell_data()

        if status_results is True:
            config_results = self.read_serial_data_eg4_ll(self.command_get_config)
        else:
            return False

        if self.debug_config:
            logger.info(f'Returned: [{config_results[0:187].hex(":").upper()}]')
            logger.info(
                f'Cell Under Voltage Warning (V): {int.from_bytes(config_results[35:37], "big")/1000}'
            )
            logger.info(
                f'Cell Over Voltage Warning (V): {int.from_bytes(config_results[47:49], "big")/1000}'
            )
            logger.info(
                f'Balancer Voltage (V): {int.from_bytes(config_results[25:27], "big")/1000}'
            )
            logger.info(
                f'Balancer Difference (mV): {int.from_bytes(config_results[27:29], "big")}'
            )

        # self.MIN_CELL_VOLTAGE = int.from_bytes(config_results[35:37], "big")/1000
        # self.MAX_CELL_VOLTAGE = int.from_bytes(config_results[47:49], "big")/1000
        # self.FLOAT_CELL_VOLTAGE = MAX_CELL_VOLTAGE - .9

        self.min_battery_voltage = utils.MIN_CELL_VOLTAGE * self.cell_count
        self.max_battery_voltage = utils.MAX_CELL_VOLTAGE * self.cell_count

        self.max_battery_charge_current = utils.MAX_BATTERY_CHARGE_CURRENT
        self.max_battery_discharge_current = utils.MAX_BATTERY_DISCHARGE_CURRENT

        # self.balancer_voltage = int.from_bytes(config_results[25:27], "big")/1000
        # self.balancer_current_delta = int.from_bytes(config_results[27:29], "big")/1000

        return True

    def refresh_data(self):
        # call all functions that will refresh the battery data.
        # This will be called for every iteration (1 second)
        # Return True if success, False for failure
        result = self.read_cell_data()
        if result is False:
            return False

        return True

    def read_gen_data(self):

        result = self.read_serial_data_eg4_ll(self.command_get_version)

        if result is False:
            return False

        self.version = (self.BATTERYTYPE + " ver ( " + str(result[0:29]), "utf-8" + ")")
        self.custom_field = result[2:27].decode("utf-8")
        self.hardware_version = result[27:33].decode("utf-8")
        self.serial_number = result[33:49].decode("utf-8")

        return True

    def read_cell_data(self):
        packet = self.read_serial_data_eg4_ll(self.command_get_stats)

        if packet is False:
            return False

        if self.debug_hex:
            logger.info("===== BMS Com Raw - Parsed =====")
            logger.info(f'Battery Voltage Raw: {packet[3:5].hex(":").upper()}')
            logger.info(f'Current RAW: {packet[5:7].hex(":").upper()}')
            logger.info(f'Capacity Remaining RAW: {packet[45:47].hex(":").upper()}')
            logger.info(f'Capacity RAW: {packet[65:69].hex(":").upper()}')
            logger.info(f'Cell Count RAW: {packet[75:77].hex(":").upper()}')
            logger.info(f'Max Charge Current RAW: {packet[47:49].hex(":").upper()}')
            logger.info(f'SoC RAW: {packet[51:53].hex(":").upper()}')
            logger.info(f'SoH Raw: {packet[49:51].hex(":").upper()}')
            logger.info(f'Cycles RAW: {packet[61:65].hex(":").upper()}')
            logger.info("======= TEMP RAW =======")
            logger.info(f'Temp Sensor Bits: {packet[69:77].hex(":").upper()}')
            logger.info(f'Temp 1 RAW: {packet[39:41].hex(":").upper()}')
            logger.info(f'Temp 2 RAW: {packet[69:70].hex(":").upper()}')
            logger.info(f'Temp 3 RAW: {packet[70:71].hex(":").upper()}')
            logger.info(f'Avg Temp Raw: {packet[41:43].hex(":").upper()}')
            logger.info(f'Temp Max Raw: {packet[43:45].hex(":").upper()}')

        self.voltage = int.from_bytes(packet[3:5], "big") / 100
        self.current = int.from_bytes(packet[5:7], "big", signed=True) / 100
        self.capacity_remain = int.from_bytes(packet[45:47], "big")
        self.capacity = int.from_bytes(packet[65:69], "big") / 3600 / 1000
        self.max_battery_charge_current = int.from_bytes(packet[47:49], "big")
        self.soc = int.from_bytes(packet[51:53], "big")
        self.soh = int.from_bytes(packet[49:51], "big")
        self.cycles = int.from_bytes(packet[61:65], "big")
        self.temp1 = int.from_bytes(packet[39:41], "big", signed=True)
        self.temp2 = int.from_bytes(packet[69:70], "big", signed=True)
        self.temp_mos = int.from_bytes(packet[70:71], "big", signed=True)
        self.cell_count = int.from_bytes(packet[75:77], "big")
        status_hex = packet[54:55].hex().upper()
        warning_hex = packet[55:57].hex().upper()
        protection_hex = packet[57:59].hex().upper()
        error_hex = packet[59:61].hex().upper()
        heater_status = packet[53:54].hex().upper()

        cell_average = cell_total = 0
        cell_start_pos = 7
        cell_end_pos = 9
        self.cell_min = 3.6
        self.cell_max = 0

        if len(self.cells) != self.cell_count:
            self.cells = []
            for idx in range(self.cell_count):
                self.cells.append(Cell(False))

        for c in range(self.cell_count):
            cell_voltage = (
                int.from_bytes(packet[cell_start_pos:cell_end_pos], "big") / 1000
            )
            if self.cell_min > cell_voltage:
                self.cell_min = cell_voltage
            if self.cell_max < cell_voltage:
                self.cell_max = cell_voltage
            cell_total += cell_voltage
            cell_average += cell_voltage
            cell_start_pos += 2
            cell_end_pos += 2
            self.cells[c].voltage = cell_voltage
        self.cell_average = cell_average / self.cell_count

        if status_hex == "00":
            status_code = "Standby"
        elif status_hex == "01":
            status_code = "Charging"
        elif status_hex == "02":
            status_code = "Discharging"
        elif status_hex == "04":
            status_code = "Protect"
        elif status_hex == "08":
            status_code = "Charging Limit"

        if heater_status == "00":
            heater_state = False
        elif heater_status == "80":
            heater_state = True

        if warning_hex == "0000":
            warning_alarm = f"No Warnings - {warning_hex}"
        elif warning_hex == "0001":
            warning_alarm = f"Warning: {warning_hex} - Pack Over Voltage"
            self.voltage_high = 1
        elif warning_hex == "0002":
            warning_alarm = f"Warning: {warning_hex} - Cell Over Voltage"
            self.voltage_cell_high = 1
        elif warning_hex == "0004":
            warning_alarm = f"Warning: {warning_hex} - Pack Under Voltage"
            self.voltage_low = 1
        elif warning_hex == "0008":
            warning_alarm = f"Warning: {warning_hex} - Cell Under Voltage"
            self.voltage_cell_low = 1
        elif warning_hex == "0010":
            warning_alarm = f"Warning: {warning_hex} - Charge Over Current"
            self.current_over = 1
        elif warning_hex == "0020":
            warning_alarm = f"Warning: {warning_hex} - Discharge Over Current"
            self.current_over = 1
        elif warning_hex == "0040":
            warning_alarm = f"Warning: {warning_hex} - Ambient High Temp"
            self.temp_high_internal = 1
        elif warning_hex == "0080":
            warning_alarm = f"Warning: {warning_hex} - Mosfets High Temp"
            self.temp_high_internal = 1
        elif warning_hex == "0100":
            warning_alarm = f"Warning: {warning_hex} - Charge Over Temp"
            self.temp_high_charge = 1
        elif warning_hex == "0200":
            warning_alarm = f"Warning: {warning_hex} - Discharge Over Temp"
            self.temp_high_discharge = 1
        elif warning_hex == "0400":
            warning_alarm = f"Warning: {warning_hex} - Charge Under Temp"
            self.temp_low_charge = 1
        elif warning_hex == "1000":
            warning_alarm = f"Warning: {warning_hex} - Low Capacity"
            self.soc_low = 1
        elif warning_hex == "2000":
            warning_alarm = f"Warning: {warning_hex} - Float Stoped"
        elif warning_hex == "4000":
            warning_alarm = f"Warning: {warning_hex} - UNKNOWN"
            self.internal_failure = 1

        if protection_hex == "0000":
            protection_alarm = f"No Protection Events - {protection_hex}"
        elif protection_hex == "0001":
            protection_alarm = f"Protection: {protection_hex} - Pack Over Voltage"
            self.voltage_high = 2
        elif protection_hex == "0002":
            protection_alarm = f"Protection: {protection_hex} - Cell Over Voltage"
            self.voltage_cell_high = 2
        elif protection_hex == "0004":
            protection_alarm = f"Protection: {protection_hex} - Pack Under Voltage"
            self.voltage_low = 2
        elif protection_hex == "0008":
            protection_alarm = f"Protection: {protection_hex} - Cell Under Voltage"
            self.voltage_cell_low = 2
        elif protection_hex == "0010":
            protection_alarm = f"Protection: {protection_hex} - Charge Over Current"
            self.current_over = 2
        elif protection_hex == "0020":
            protection_alarm = f"Protection: {protection_hex} - Discharge Over Current"
            self.current_over = 2
        elif protection_hex == "0040":
            protection_alarm = f"Protection: {protection_hex} - High Ambient Temp"
            self.temp_high_internal = 2
        elif protection_hex == "0080":
            protection_alarm = f"Protection: {protection_hex} - Mosfets High Temp"
            self.temp_high_internal = 2
        elif protection_hex == "0100":
            protection_alarm = f"Protection: {protection_hex} - Charge Over Temp"
            self.temp_high_charge = 2
        elif protection_hex == "0200":
            protection_alarm = f"Protection: {protection_hex} - Discharge Over Temp"
            self.temp_high_discharge = 2
        elif protection_hex == "0400":
            protection_alarm = f"Protection: {protection_hex} - Charge Under Temp"
            self.temp_low_charge = 2
        elif protection_hex == "0800":
            protection_alarm = f"Protection: {protection_hex} - Discharge Under Temp"
            self.temp_low_charge = 2
        elif protection_hex == "1000":
            protection_alarm = f"Protection: {protection_hex} - Low Capacity"
            self.soc_low = 2
        elif protection_hex == "2000":
            protection_alarm = f"Protection: {protection_hex} - Discharge SC"

        if error_hex == "0000":
            error = f"No Errors - {error_hex}"
        elif error_hex == "0001":
            error = f"Error: {error_hex} - Voltage Error"
        elif error_hex == "0002":
            error = f"Error: {error_hex} - Temperature Error"
        elif error_hex == "0004":
            error = f"Error: {error_hex} - Current Flow Error"
        elif error_hex == "0010":
            error = f"Error: {error_hex} - Cell Unbalanced"

        logger.info("===== HW Info =====")
        logger.info(f"Battery Make/Model: {str(self.custom_field)}")
        logger.info(f"Hardware Version: {str(self.hardware_version)}")
        logger.info(f"Serial Number: {str(self.unique_identifier())}")
        logger.info("===== BMS Data =====")
        logger.info(
            "Cell Total Voltage: "
            + "%.3fv" % cell_total
            + " | Current: "
            + str(self.current)
            + "A"
        )
        logger.info(f"Capacity Left: {self.capacity_remain} of {self.capacity} AH")
        logger.info(f"SoC: {self.soc}% - {status_code}")
        logger.info("===== DVCC State =====")
        logger.info(f"DVCC Charger Mode: {self.charge_mode}")
        logger.info(f"DVCC Charge Voltage: {self.control_voltage}v")
        logger.info(
            f"Charge Current: {self.control_charge_current} | Discharge Current: {self.control_discharge_current}"
        )
        logger.info(
            f"Charge Limit: {self.charge_limitation} | Discharge Limit: {self.discharge_limitation}"
        )
        logger.info("===== Warning/Alarms =====")
        logger.info(f" {warning_alarm}")
        logger.info(f" {protection_alarm}")
        logger.info(f" {error}")
        logger.info("===== Temp =====")
        logger.info(
            f"Temp 1: {self.temp1}c | Temp 2: {self.temp2}c | Temp Mos: {self.temp_mos}c"
        )
        logger.info(
            f'Avg: {int.from_bytes(packet[41:43], "big", signed=True)}c | '
            + f'Temp Max: {int.from_bytes(packet[43:45], "big", signed=True)}c'
        )
        logger.info(f"Heater Status: {heater_state}")
        logger.info("===== Battery Stats =====")
        logger.info(f"SoH: {self.soh}% | Cycle Count: {self.cycles}")
        logger.info(f"Max Charging Current: {self.max_battery_charge_current} A")
        logger.info("===== Cell Stats =====")
        for c in range(self.cell_count):
            logger.info(f"Cell {c} Voltage: {self.cells[c].voltage}")
        logger.info(
            f"Cell Max/Min/Diff: ({self.cell_max}/{self.cell_min}/{round((self.cell_max-self.cell_min), 3)})v"
        )

        return True

    def read_temp_data(self):
        # Temp Data is collected when the cell data is read
        result = self.read_cell_data()
        if result is False:
            return False
        return True

    def get_balancing(self):
        # if (self.cell_max - self.cell_min) >= self.balancer_current_delta:
        #    if self.cell_max >= self.balancer_voltage:
        #        self.balancing = 1
        #        logger.info(f'*** Balancing Battery ***')
        # else:
        #    self.balancing = 0
        #    logger.info(f'*** Not Balancing Battery ***')
        # if (
        #     self.cell_average > self.balancer_voltage
        #     and round((self.cell_max - self.cell_min), 3) <= self.balancer_current_delta
        # ):
        #     self.balacing = 2
        #     logger.info(f'*** Finished Balancing Battery ***')
        #     return self.balancing

        return 1 if self.balancing or self.balancing == 2 else 0

    def read_bms_config(self):
        logger.info("Executed read_bms_config function... function needs to be written")
        return True

    def generate_command(self, command):
        # buffer = bytearray(self.command_address)
        # buffer += command
        return command

    def read_serial_data_eg4_ll(self, command):
        # use the read_serial_data() function to read the data and then do BMS specific checks (crc, start bytes, etc
        if self.debug:
            logger.info(f"Modbus CMD Address: {hex(self.command_address[0]).upper()}")
            logger.info(f'Executed Command: {command.hex(":").upper()}')

        data = read_serial_data(
            command, self.port, self.baud_rate, self.LENGTH_POS, self.LENGTH_CHECK
        )
        if data is False:
            logger.debug("read_serial_data_eg4_ll::Serial Data is Bad")
            return False
        else:
            if self.debug:
                logger.info(f'Returned: [{data.hex(":").upper()}]')

        # Its not quite modbus, but psuedo modbus'ish'
        modbus_address, modbus_type, modbus_cmd, modbus_packet_length = unpack_from(
            "BBBB", data
        )

        if self.debug:
            logger.info(f"Modbus Address: {modbus_address} [{hex(modbus_address)}]")
            logger.info(f"Modbus Type   : {modbus_type} [{hex(modbus_type)}]")
            logger.info(f"Modbus Command: {modbus_cmd} [{hex(modbus_cmd)}]")
            logger.info(
                f"Modbus PackLen: {modbus_packet_length} [{hex(modbus_packet_length)}]"
            )
            logger.info(f'Modbus Packet : [ {data.hex(":").upper()} ]')

        if modbus_type == 3:
            logger.info("== Modbus packet good ==")
            return data  # Pass the full packet from the BMS
        else:
            logger.error(">>> ERROR: Incorrect Reply")
            logger.info(f"Modbus Type   : {modbus_type} [{hex(modbus_type)}]")
            logger.info(
                f"Modbus PackLen: {modbus_packet_length} [{hex(modbus_packet_length)}]"
            )
            return False
