# -*- coding: utf-8 -*-

# Undeprecate Revov driver
from battery import Protection, Battery, Cell
from utils import *
from struct import *
import struct
import utils

#    Author: L Sheed / https://github.com/csloz
#    Date: 5 Jun 2023
#    Version 0.2
#     Cell Voltage Implemented
#     Hardware Name Implemented
#     Hardware Revision Implemented
#     Battery Voltage added (and corrected using bit masks)


class Revov(Battery):
    def __init__(self, port, baud, address):
        super(Revov, self).__init__(port, baud, address)
        self.type = self.BATTERYTYPE
        self.command_address = address  # 7C on my tianpower...

    # Modbus uses 7C call vs Lifepower 7E, as return values do not correlate to the Lifepower ones if 7E is used.
    # at least on my own BMS.
    debug = True  # Set to true for wordy debugging in logs
    balancing = 0
    BATTERYTYPE = "Revov"
    LENGTH_CHECK = 0
    LENGTH_POS = 3  # offset starting from 0
    LENGTH_FIXED = -1

    command_address = b"\0x7C"  # Default unless overridden
    command_get_version = b"\x01\x42\x00\x80\x0D"  # Get version number
    command_get_model = b"\x01\x33\x00\xFE\x0D"  # Get model number
    command_one = b"\x01\x06\x00\xF8\x0D"  # returns 4 bytes
    command_two = b"\x01\x01\x00\x02\x0D"  # returns a ton of data

     def test_connection(self):
            # call a function that will connect to the battery, send a command and retrieve the result.
        # The result or call should be unique to this BMS. Battery name or version, etc.
        # Return True if success, False for failure
        result = False
        try:
            result = self.read_gen_data()
            # get first data to show in startup log
            if result:
                self.refresh_data()
        except Exception as err:
            logger.error(f"Unexpected {err=}, {type(err)=}")
            result = False

        return result

    def get_settings(self):
        # After successful  connection get_settings will be call to set up the battery.
        # Return True if success, False for failure

        self.max_battery_charge_current = utils.MAX_BATTERY_CHARGE_CURRENT
        self.max_battery_discharge_current = utils.MAX_BATTERY_DISCHARGE_CURRENT
        self.poll_interval = 2000

        return True

    def refresh_data(self):
        # call all functions that will refresh the battery data.
        # This will be called for every iteration (1 second)
        # Return True if success, False for failure
        result = self.read_cell_data()
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


    def read_cell_data(self):
        status_data = self.read_serial_data_revov(self.command_two)

        if status_data is False:
            return False

        groups = []
        i = 0
        for j in range(0, 15):
            # groups are formatted like:
            # {group number} {length} ...length shorts up to pos 10, then longs after...
            # So the first group might be (2 byte x 2)
            # 01 02 0a 0b 0c 0d
            # Second group might be (4 byte long x 1)
            # 10 01 00 00 00 00

            if (j > 9 and j < 15):
                byte_size = 4
            else:
                byte_size = 2
            group_len = status_data[i + 1]
            end = i + 2 + (group_len * byte_size)
            group_payload = status_data[i + 2: end]
            groups.append(
                [
                    unpack_from(">H", group_payload, i)[0]
                    for i in range(0, len(group_payload), 2)
                ]
            )
            i = end
            if (self.debug):
                logger.info(f'Pos:{i} CMD ID: {j} Len: {group_len} Size: {byte_size}')

        # Total Cells
        self.cell_count = len(groups[0])
        self.max_battery_voltage = utils.MAX_CELL_VOLTAGE * self.cell_count
        self.min_battery_voltage = utils.MIN_CELL_VOLTAGE * self.cell_count
        if (self.debug):
            logger.info(f'Cell Count: {self.cell_count}')

        # Per Cell Value
        self.cells = [Cell(True) for _ in range(0, self.cell_count)]
        for i, cell in enumerate(self.cells):
            # there is a situation where 2 MSB bit of the high byte may come set
            # I got that when I got a high voltage alarm from the unit.
            # make sure that bit is 0, by doing an AND with 32767, 16383 (00111111 1111111)
            cell.voltage = (groups[0][i] & 32767 & 16383) / 1000
            if (self.debug):
                logger.info(f'Cell {i}: {cell.voltage}')
       # Current
        self.current = (30000 - groups[1][0]) / 100
        if (self.debug):
            logger.info(f'Current: {self.current}')

        # State of charge
        self.soc = groups[2][0] / 100
        if (self.debug):
            logger.info(f'SoC: {self.soc}')

        # Full battery capacity
        self.capacity = groups[3][0] / 100
        if (self.debug):
            logger.info(f'Capacity: {self.capacity}')

        # 7E for Lifepower
        # 7C for Tianpower BMS (older Revov)

        #better to rewrite this to do length of groups[4] and loop for values.
        if (self.command_address[0] == 0x7E):
            # Temperature To Do; current code offsets or sensor counts are incorrect for the TianPower version I have.
            self.temp_sensors = 6
            self.temp1 = (groups[4][0] & 0xFF) - 50
            self.temp2 = (groups[4][1] & 0xFF) - 50
            self.temp3 = (groups[4][2] & 0xFF) - 50
            self.temp4 = (groups[4][3] & 0xFF) - 50
            self.temp5 = (groups[4][4] & 0xFF) - 50
            self.temp6 = (groups[4][5] & 0xFF) - 50
            logger.info(f'Temp Sensors: {self.temp_sensors} T1:{self.temp1} T2:{self.temp2} T3:{self.temp3} T4:{self.temp4} T5:{self.temp5} T6:{self.temp6}')
        elif (self.command_address[0] == 0x7C):
            self.temp_sensors = 3
            self.temp1 = (groups[4][0] & 0xFF) - 50
            self.temp2 = (groups[4][1] & 0xFF) - 50
            self.temp3 = (groups[4][2] & 0xFF) - 50
            logger.info(f'Temp Sensors: Total:{self.temp_sensors} T1:{self.temp1} T2:{self.temp2} T3:{self.temp3}')

        # 4th bit: Over Current Protection
        self.protection.current_over = 2 if (groups[5][1] & 0b00001000) > 0 else 0
        # 5th bit: Over voltage protection
        self.protection.voltage_high = 2 if (groups[5][1] & 0b00010000) > 0 else 0
        # 6th bit: Under voltage protection
        self.protection.voltage_low = 2 if (groups[5][1] & 0b00100000) > 0 else 0
        # 7th bit: Charging over temp protection
        self.protection.temp_high_charge = 2 if (groups[5][1] & 0b01000000) > 0 else 0
        # 8th bit: Charging under temp protection
        self.protection.temp_low_charge = 2 if (groups[5][1] & 0b10000000) > 0 else 0
        if (self.debug):
            logger.info(f'Protection')

        # Cycle counter
        self.cycles = groups[6][0]
        if (self.debug):
            logger.info(f'Cycles: {self.cycles}')

        # Voltage
        self.voltage = groups[7][0] / 100
        if (self.debug):
            logger.info(f'Voltage: {self.voltage}')

        return True

    def read_temp_data(self):
        # disabled for now. As mapped in main
        return True
        

    def get_balancing(self):
        return 1 if self.balancing or self.balancing == 2 else 0

    def read_bms_config(self):
        return True

    def generate_command(self, command):
        buffer = bytearray(self.command_address)
        buffer += command
        return buffer
    
    def read_serial_data_revov(self, command):
        # use the read_serial_data() function to read the data and then do BMS spesific checks (crc, start bytes, etc)

        if (self.debug):
            logger.info(f'Modbus CMD Address: {hex(self.command_address[0]).upper()}')

        data = read_serial_data(
            self.generate_command(command),
            self.port,
            self.baud_rate,
            self.LENGTH_POS,
            self.LENGTH_CHECK
        )

        if data is False:
            logger.error("read_serial_data_revov::Serial Data is Bad")
            return False

        # Its not quite modbus, but psuedo modbus'ish'
        modbus_address, modbus_type, modbus_cmd, modbus_packet_length = unpack_from(
            "BBBB", data
        )

        if (self.debug):
            logger.info(f'Modbus Address: {modbus_address} [{hex(modbus_address)}]')
            logger.info(f'Modbus Type   : {modbus_type} [{hex(modbus_type)}]')
            logger.info(f'Modbus Command: {modbus_cmd} [{hex(modbus_cmd)}]')
            logger.info(f'Modbus PackLen: {modbus_packet_length} [{hex(modbus_packet_length)}]')
            logger.info(f'Modbus Packet : [ {data.hex(":").upper()} ]')

        # If address is correct and the command is correct then its a good packet
        if modbus_type == 1 and modbus_address == self.command_address[0]:
            logger.info("== Modbus packet good ==")
            return data[4: modbus_packet_length + 4]
        else:
            logger.error(">>> ERROR: Incorrect Reply")
            return False


