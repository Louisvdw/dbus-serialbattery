# -*- coding: utf-8 -*-

# Deprecate Revov driver - replaced by LifePower
# https://github.com/Louisvdw/dbus-serialbattery/pull/353/commits/c3ac9558fc86b386e5a6aefb313408165c86d240

from battery import Protection, Battery, Cell
from utils import *
from struct import *
import struct
import sys

#    Author: L Sheed
#    Date: 3 May 2022
#    Version 0.1.3
#     Cell Voltage Implemented
#     Hardware Name Implemented
#     Hardware Revision Implemented
#     Battery Voltage added (but not correct!)
#     Added additional binary logging so I can try spot what bits are used for RED errors
#     To do:
#     SOC, Error Codes, Other variables


class Revov(Battery):
    def __init__(self, port, baud, address):
        super(Revov, self).__init__(port, baud, address)
        self.type = self.BATTERYTYPE
        self.soc = 100
        self.voltage = None
        self.current = None
        self.cell_min_voltage = None
        self.cell_max_voltage = None
        self.cell_min_no = None
        self.cell_max_no = None
        self.cell_count = 16
        self.cells = []
        self.cycles = None

    BATTERYTYPE = "Revov"
    LENGTH_CHECK = 0
    LENGTH_POS = 3  # offset starting from 0
    LENGTH_FIXED = -1

    # setup the variables being looked for

    command_get_version = b"\x7C\x01\x42\x00\x80\x0D"  # Get version number
    command_get_model = b"\x7C\x01\x33\x00\xFE\x0D"  # Get model number
    command_one = b"\x7C\x01\x06\x00\xF8\x0D"  # returns 4 bytes
    command_two = b"\x7C\x01\x01\x00\x02\x0D"  # returns a ton of data

    def test_connection(self):
        # call a function that will connect to the battery, send a command and retrieve the result.
        # The result or call should be unique to this BMS. Battery name or version, etc.
        # Return True if success, False for failure
        result = False
        try:
            result = self.read_gen_data()
            # get first data to show in startup log
            result = result and self.refresh_data()
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
        # Set the current limits, populate cell count, etc
        # Return True if success, False for failure

        self.max_battery_charge_current = MAX_BATTERY_CHARGE_CURRENT
        self.max_battery_discharge_current = MAX_BATTERY_DISCHARGE_CURRENT
        self.max_battery_voltage = MAX_CELL_VOLTAGE * self.cell_count
        self.min_battery_voltage = MIN_CELL_VOLTAGE * self.cell_count
        # Need to fix to use correct value will do later.  hard coded for now
        for c in range(self.cell_count):
            self.cells.append(Cell(False))
        return True

    def refresh_data(self):
        # call all functions that will refresh the battery data.
        # This will be called for every iteration (1 second)
        # Return True if success, False for failure
        result = self.read_soc_data()
        result = result and self.read_cell_data()
        # result = result and self.read_temp_data()
        return result

    def read_gen_data(self):
        model = self.read_serial_data_revov(self.command_get_model)

        # check if connection success
        if model is False:
            return False

        self.version = self.BATTERYTYPE + " " + str(model, "utf-8")
        logger.error(self.version)

        version = self.read_serial_data_revov(self.command_get_version)
        if version is False:
            return False

        self.hardware_version = (
            self.BATTERYTYPE + " ver ( " + str(version, "utf-8") + ")"
        )
        logger.error(self.hardware_version)

        # At moment run solely for logging purposes so i can compare
        one = self.read_serial_data_revov(self.command_one)
        two = self.read_serial_data_revov(self.command_two)

        return True

    def read_soc_data(self):
        # self.soc=70
        self.voltage = 55
        self.current = 5

        return True

    # soc_data = self.read_serial_data_revov(self.command_soc)
    # check if connection success
    # if soc_data is False:
    #    return False

    # current, voltage, self.capacity_remain = unpack_from('>hhL', soc_data)
    # self.current = current / 100
    # self.voltage = voltage / 10
    # self.soc = self.capacity_remain / self.capacity * 100
    # return True

    def read_cell_data(self):
        packet = self.read_serial_data_revov(self.command_two)

        if packet is False:
            return False

        # cell_volt_data = self.read_serial_data_revov(self.command_cell_voltages)
        # cell_temp_data = self.read_serial_data_revov(self.command_cell_temps)

        self.voltage = unpack_from(">H", packet, 72)[0]
        if self.voltage > 9999:
            self.voltage = self.voltage / 1000
        elif self.voltage > 999:
            self.voltage = self.voltage / 100
        logger.warn("Voltage Data: [" + str(self.voltage) + "v]")

        self.cycles = unpack_from(">H", packet, 68)[0]
        logger.warn("Battery Cycles: [" + str(self.cycles) + "]")

        self.capacity = unpack_from(">H", packet, 44)[0]
        self.capacity = self.capacity / 100
        logger.warn("Battery Capacity: [" + str(self.capacity) + "Ah]")

        # serial returns from offset 4 onwards, so our packet data will start with module #, then cell count.
        cell_count = unpack_from(">B", packet, 1)[0]
        self.cell_count = cell_count

        logger.warn("Cell count: [" + str(self.cell_count) + "]")

        cell_volt_data = packet[
            2 : (self.cell_count * 2) + 2
        ]  # 16 2 byte values from pos 3 (index 2)
        logger.warn("Raw Cell Data: [" + str(cell_volt_data.hex(":")).upper() + "]")

        # first, second = unpack_from ('>HH',cell_volt_data)
        # logger.warn ("First Cell: " + str(first) + " Second Cell: " + str(second))

        cell_total = 0

        for c in range(self.cell_count):
            try:
                cell_volts = unpack_from(">H", cell_volt_data, c * 2)[0]
                # raw_data = cell_volt_data[c*2:2]
                # logger.warn ("Cell [" + str(c+1) + "] " + str(cell_volts) +  " " + str(raw_data.hex(':')).upper() )
                # hacky divisor code
                if cell_volts > 9999:
                    self.cells[c].voltage = cell_volts / 10000
                elif cell_volts > 999:
                    self.cells[c].voltage = cell_volts / 1000
                # Show Cell #, Voltage to 4DP, Hex and Binary value
                logger.warn(
                    "Cell ["
                    + "%02d" % (c + 1)
                    + "] "
                    + "%.3f" % self.cells[c].voltage
                    + "v "
                    + "0x%04X" % cell_volts
                    + " "
                    + str(bin(cell_volts))
                )
                cell_total = cell_total + self.cells[c].voltage
            except struct.error:
                self.cells[c].voltage = 0

        logger.warn("Cell Total: " + "%.2fv" % cell_total)
        return True

    def read_temp_data(self):
        return True
        # disabled for now.  I need to find what bytes map to the 2 temp sensors

        temp1 = self.read_serial_data_revov(self.command_bms_temp1)
        temp2 = self.read_serial_data_revov(self.command_bms_temp2)
        if temp1 is False:
            return False
        self.temp1 = unpack(">H", temp1)[0] / 10
        self.temp2 = unpack(">H", temp2)[0] / 10

        return True

    def read_bms_config(self):
        return True

    def read_serial_data_revov(self, command):
        # use the read_serial_data() function to read the data and then do BMS spesific checks (crc, start bytes, etc)
        data = read_serial_data(
            command, self.port, self.baud_rate, self.LENGTH_POS, self.LENGTH_CHECK
        )

        if data is False:
            logger.debug("read_serial_data_revov::Serial Data is Bad")
            return False

        # Its not quite modbus, but psuedo modbus'ish'
        modbus_address, modbus_type, modbus_cmd, modbus_packet_length = unpack_from(
            "BBBB", data
        )

        logger.warn("Modbus Address: " + str(modbus_address))
        logger.warn("Modbus Type   : " + str(modbus_type))
        logger.warn("Modbus Command: " + str(modbus_cmd))
        logger.warn("Modbus PackLen: " + str(modbus_packet_length))
        logger.warn("Modbus Packet : [" + str(data.hex(":")).upper() + "]")

        # If address is correct and the command is correct then its a good packet
        if modbus_type == 1 and modbus_address == 124:
            logger.warn("== Modbus packet good ==")
            return data[4 : modbus_packet_length + 4]
        else:
            logger.error(">>> ERROR: Incorrect Reply")
            return False
