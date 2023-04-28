# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from battery import Battery, Cell
from utils import read_serial_data, logger
import utils
from struct import unpack_from
import re


class Lifepower(Battery):
    def __init__(self, port, baud, address):
        super(Lifepower, self).__init__(port, baud, address)
        self.type = self.BATTERYTYPE

    command_general = b"\x7E\x01\x01\x00\xFE\x0D"
    command_hardware_version = b"\x7E\x01\x42\x00\xFC\x0D"
    command_firmware_version = b"\x7E\x01\x33\x00\xFE\x0D"
    balancing = 0
    BATTERYTYPE = "EG4 Lifepower"
    LENGTH_CHECK = 5
    LENGTH_POS = 3
    LENGTH_FIXED = None

    def test_connection(self):
        # call a function that will connect to the battery, send a command and retrieve the result.
        # The result or call should be unique to this BMS. Battery name or version, etc.
        # Return True if success, False for failure
        result = False
        try:
            result = self.read_status_data()
        except Exception as err:
            logger.error(f"Unexpected {err=}, {type(err)=}")
            result = False

        return result

    def get_settings(self):
        # After successful  connection get_settings will be call to set up the battery.
        # Set the current limits, populate cell count, etc
        # Return True if success, False for failure
        self.max_battery_current = utils.MAX_BATTERY_CURRENT
        self.max_battery_discharge_current = utils.MAX_BATTERY_DISCHARGE_CURRENT
        hardware_version = self.read_serial_data_eg4(self.command_hardware_version)
        if hardware_version:
            # I get some characters that I'm not able to figure out the encoding, probably chinese so I discard it
            # Also remove any special character that is not printable or make no sense.
            self.hardware_version = re.sub(
                r"[^a-zA-Z0-9-._ ]",
                "",
                str(hardware_version, encoding="utf-8", errors="ignore"),
            )
            logger.info("Hardware Version:" + self.hardware_version)

        version = self.read_serial_data_eg4(self.command_firmware_version)
        if version:
            self.version = re.sub(
                r"[^a-zA-Z0-9-._ ]", "", str(version, encoding="utf-8", errors="ignore")
            )
            logger.info("Firmware Version:" + self.version)

        # polling every second seems to create some error messages
        # change to 2 seconds
        self.poll_interval = 2000
        return True

    def refresh_data(self):
        # call all functions that will refresh the battery data.
        # This will be called for every iteration (1 second)
        # Return True if success, False for failure
        return self.read_status_data()

    def read_status_data(self):
        status_data = self.read_serial_data_eg4(self.command_general)
        # check if connection success
        if status_data is False:
            return False

        # Data pulled from https://github.com/slim-bean/powermon

        groups = []
        i = 4
        for j in range(0, 10):
            # groups are formatted like:
            # {group number} {length} ...length shorts...
            # So the first group might be:
            # 01 02 0a 0b 0c 0d
            group_len = status_data[i + 1]
            end = i + 2 + (group_len * 2)
            group_payload = status_data[i + 2 : end]
            groups.append(
                [
                    unpack_from(">H", group_payload, i)[0]
                    for i in range(0, len(group_payload), 2)
                ]
            )
            i = end

        # Cells
        self.cell_count = len(groups[0])
        self.max_battery_voltage = utils.MAX_CELL_VOLTAGE * self.cell_count
        self.min_battery_voltage = utils.MIN_CELL_VOLTAGE * self.cell_count

        self.cells = [Cell(True) for _ in range(0, self.cell_count)]
        for i, cell in enumerate(self.cells):
            # there is a situation where the MSB bit of the high byte may come set
            # I got that when I got a high voltage alarm from the unit.
            # make sure that bit is 0, by doing an AND with 32767 (01111111 1111111)
            cell.voltage = (groups[0][i] & 32767) / 1000

        # Current
        self.current = (30000 - groups[1][0]) / 100

        # State of charge
        self.soc = groups[2][0] / 100

        # Full battery capacity
        self.capacity = groups[3][0] / 100

        # Temperature
        self.temp_sensors = 6
        self.temp1 = (groups[4][0] & 0xFF) - 50
        self.temp2 = (groups[4][1] & 0xFF) - 50
        self.temp3 = (groups[4][2] & 0xFF) - 50
        self.temp4 = (groups[4][3] & 0xFF) - 50
        self.temp5 = (groups[4][4] & 0xFF) - 50
        self.temp6 = (groups[4][5] & 0xFF) - 50

        # Alarms
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

        # Cycle counter
        self.cycles = groups[6][0]

        # Voltage
        self.voltage = groups[7][0] / 100
        return True

    def get_balancing(self):
        return 1 if self.balancing or self.balancing == 2 else 0

    def read_serial_data_eg4(self, command):
        # use the read_serial_data() function to read the data and then do BMS
        # specific checks (crc, start bytes, etc)
        data = read_serial_data(
            command,
            self.port,
            self.baud_rate,
            self.LENGTH_POS,
            self.LENGTH_CHECK,
            self.LENGTH_FIXED,
        )
        if data is False:
            logger.error(">>> ERROR: Incorrect Data")
            return False

        # 0x0D always terminates the response
        if data[-1] == 13:
            return data
        else:
            logger.error(">>> ERROR: Incorrect Reply")
            return False
