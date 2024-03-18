# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from battery import Battery, Cell
from utils import (
    is_bit_set,
    logger,
    MAX_BATTERY_CHARGE_CURRENT,
    MAX_BATTERY_DISCHARGE_CURRENT,
    MAX_CELL_VOLTAGE,
    MIN_CELL_VOLTAGE,
    JKBMS_CAN_CELL_COUNT,
    zero_char,
)
from struct import unpack_from
import can
import time

"""
https://github.com/Louisvdw/dbus-serialbattery/compare/dev...IrisCrimson:dbus-serialbattery:jkbms_can

# Restrictions seen from code:
-
"""


class Jkbms_Can(Battery):
    def __init__(self, port, baud, address):
        super(Jkbms_Can, self).__init__(port, baud, address)
        self.can_bus = False
        self.cell_count = 1
        self.poll_interval = 1500
        self.type = self.BATTERYTYPE
        self.last_error_time = time.time()
        self.error_active = False

    def __del__(self):
        if self.can_bus:
            self.can_bus.shutdown()
            self.can_bus = False
            logger.debug("bus shutdown")

    BATTERYTYPE = "Jkbms_Can"
    CAN_BUS_TYPE = "socketcan"

    CURRENT_ZERO_CONSTANT = 400
    BATT_STAT = "BATT_STAT"
    CELL_VOLT = "CELL_VOLT"
    CELL_TEMP = "CELL_TEMP"
    ALM_INFO = "ALM_INFO"

    MESSAGES_TO_READ = 100

    # B2A... Black is using 0x0XF4
    # B2A... Silver is using 0x0XF5
    # See https://github.com/Louisvdw/dbus-serialbattery/issues/950
    CAN_FRAMES = {
        BATT_STAT: [0x02F4, 0x02F5],
        CELL_VOLT: [0x04F4, 0x04F5],
        CELL_TEMP: [0x05F4, 0x05F5],
        ALM_INFO: [0x07F4, 0x07F5]
    }

    def test_connection(self):
        # call a function that will connect to the battery, send a command and retrieve the result.
        # The result or call should be unique to this BMS. Battery name or version, etc.
        # Return True if success, False for failure
        return self.read_status_data()

    def get_settings(self):
        # After successful  connection get_settings will be call to set up the battery.
        # Set the current limits, populate cell count, etc
        # Return True if success, False for failure
        self.cell_count = JKBMS_CAN_CELL_COUNT
        self.max_battery_charge_current = MAX_BATTERY_CHARGE_CURRENT
        self.max_battery_discharge_current = MAX_BATTERY_DISCHARGE_CURRENT
        self.max_battery_voltage = MAX_CELL_VOLTAGE * self.cell_count
        self.min_battery_voltage = MIN_CELL_VOLTAGE * self.cell_count

        # init the cell array add only missing Cell instances
        missing_instances = self.cell_count - len(self.cells)
        if missing_instances > 0:
            for c in range(missing_instances):
                self.cells.append(Cell(False))

        self.hardware_version = "JKBMS CAN " + str(self.cell_count) + " cells"
        return True

    def refresh_data(self):
        # call all functions that will refresh the battery data.
        # This will be called for every iteration (1 second)
        # Return True if success, False for failure
        result = self.read_status_data()

        return result

    def read_status_data(self):
        status_data = self.read_serial_data_jkbms_CAN()
        # check if connection success
        if status_data is False:
            return False

        return True

    def to_fet_bits(self, byte_data):
        tmp = bin(byte_data)[2:].rjust(2, zero_char)
        self.charge_fet = is_bit_set(tmp[1])
        self.discharge_fet = is_bit_set(tmp[0])

    def to_protection_bits(self, byte_data):
        tmp = bin(byte_data | 0xFF00000000)
        pos = len(tmp)
        logger.debug(tmp)
        self.protection.cell_overvoltage = 2 if int(tmp[pos - 2 : pos], 2) > 0 else 0
        self.protection.voltage_cell_low = (
            2 if int(tmp[pos - 4 : pos - 2], 2) > 0 else 0
        )
        self.protection.voltage_high = 2 if int(tmp[pos - 6 : pos - 4], 4) > 0 else 0
        self.protection.voltage_low = 2 if int(tmp[pos - 8 : pos - 6], 2) > 0 else 0
        self.protection.cell_imbalance = 2 if int(tmp[pos - 10 : pos - 8], 2) > 0 else 0
        self.protection.current_under = 2 if int(tmp[pos - 12 : pos - 10], 2) > 0 else 0
        self.protection.current_over = 2 if int(tmp[pos - 14 : pos - 12], 2) > 0 else 0

        # there is just a BMS and Battery temp alarm (not for charg and discharge)
        self.protection.temp_high_charge = (
            2 if int(tmp[pos - 16 : pos - 14], 2) > 0 else 0
        )
        self.protection.temp_high_discharge = (
            2 if int(tmp[pos - 16 : pos - 14], 2) > 0 else 0
        )
        self.protection.temp_low_charge = (
            2 if int(tmp[pos - 18 : pos - 16], 2) > 0 else 0
        )
        self.protection.temp_low_discharge = (
            2 if int(tmp[pos - 18 : pos - 16], 2) > 0 else 0
        )
        self.protection.temp_high_charge = (
            2 if int(tmp[pos - 20 : pos - 18], 2) > 0 else 0
        )
        self.protection.temp_high_discharge = (
            2 if int(tmp[pos - 20 : pos - 18], 2) > 0 else 0
        )
        self.protection.soc_low = 2 if int(tmp[pos - 22 : pos - 20], 2) > 0 else 0
        self.protection.internal_failure = (
            2 if int(tmp[pos - 24 : pos - 22], 2) > 0 else 0
        )
        self.protection.internal_failure = (
            2 if int(tmp[pos - 26 : pos - 24], 2) > 0 else 0
        )
        self.protection.internal_failure = (
            2 if int(tmp[pos - 28 : pos - 26], 2) > 0 else 0
        )
        self.protection.internal_failure = (
            2 if int(tmp[pos - 30 : pos - 28], 2) > 0 else 0
        )

    def reset_protection_bits(self):
        self.protection.cell_overvoltage = 0
        self.protection.voltage_cell_low = 0
        self.protection.voltage_high = 0
        self.protection.voltage_low = 0
        self.protection.cell_imbalance = 0
        self.protection.current_under = 0
        self.protection.current_over = 0

        # there is just a BMS and Battery temp alarm (not for charg and discharge)
        self.protection.temp_high_charge = 0
        self.protection.temp_high_discharge = 0
        self.protection.temp_low_charge = 0
        self.protection.temp_low_discharge = 0
        self.protection.temp_high_charge = 0
        self.protection.temp_high_discharge = 0
        self.protection.soc_low = 0
        self.protection.internal_failure = 0
        self.protection.internal_failure = 0
        self.protection.internal_failure = 0
        self.protection.internal_failure = 0

    def read_serial_data_jkbms_CAN(self):
        if self.can_bus is False:
            logger.debug("Can bus init")
            # intit the can interface
            try:
                self.can_bus = can.interface.Bus(
                    bustype=self.CAN_BUS_TYPE, channel=self.port, bitrate=self.baud_rate
                )
            except can.CanError as e:
                logger.error(e)

            if self.can_bus is None:
                return False

            logger.debug("Can bus init done")

        # reset errors after timeout
        if ((time.time() - self.last_error_time) > 120.0) and self.error_active is True:
            self.error_active = False
            self.reset_protection_bits()

        # read msgs until we get one we want
        messages_to_read = self.MESSAGES_TO_READ
        while messages_to_read > 0:
            msg = self.can_bus.recv(1)
            if msg is None:
                logger.info("No CAN Message received")
                return False

            if msg is not None:
                # print("message received")
                messages_to_read -= 1
                # print(messages_to_read)
                if msg.arbitration_id in self.CAN_FRAMES[self.BATT_STAT]:
                    voltage = unpack_from("<H", bytes([msg.data[0], msg.data[1]]))[0]
                    self.voltage = voltage / 10

                    current = unpack_from("<H", bytes([msg.data[2], msg.data[3]]))[0]
                    self.current = (current / 10) - 400

                    self.soc = unpack_from("<B", bytes([msg.data[4]]))[0]

                    self.time_to_go = (
                        unpack_from("<H", bytes([msg.data[6], msg.data[7]]))[0] * 36
                    )

                    # print(self.voltage)
                    # print(self.current)
                    # print(self.soc)
                    # print(self.time_to_go)

                elif msg.arbitration_id in self.CAN_FRAMES[self.CELL_VOLT]:
                    max_cell_volt = (
                        unpack_from("<H", bytes([msg.data[0], msg.data[1]]))[0] / 1000
                    )
                    max_cell_nr = unpack_from("<B", bytes([msg.data[2]]))[0]
                    max_cell_cnt = max(max_cell_nr, self.cell_count)

                    min_cell_volt = (
                        unpack_from("<H", bytes([msg.data[3], msg.data[4]]))[0] / 1000
                    )
                    min_cell_nr = unpack_from("<B", bytes([msg.data[5]]))[0]
                    max_cell_cnt = max(min_cell_nr, max_cell_cnt)

                    if max_cell_cnt > self.cell_count:
                        self.cell_count = max_cell_cnt
                        self.get_settings()

                    for c_nr in range(len(self.cells)):
                        self.cells[c_nr].balance = False

                    if self.cell_count == len(self.cells):
                        self.cells[max_cell_nr - 1].voltage = max_cell_volt
                        self.cells[max_cell_nr - 1].balance = True

                        self.cells[min_cell_nr - 1].voltage = min_cell_volt
                        self.cells[min_cell_nr - 1].balance = True

                elif msg.arbitration_id in self.CAN_FRAMES[self.CELL_TEMP]:
                    max_temp = unpack_from("<B", bytes([msg.data[0]]))[0] - 50
                    min_temp = unpack_from("<B", bytes([msg.data[2]]))[0] - 50
                    self.to_temp(1, max_temp if max_temp <= 100 else 100)
                    self.to_temp(2, min_temp if min_temp <= 100 else 100)
                    # print(max_temp)
                    # print(min_temp)
                elif msg.arbitration_id in self.CAN_FRAMES[self.ALM_INFO]:
                    alarms = unpack_from(
                        "<L",
                        bytes([msg.data[0], msg.data[1], msg.data[2], msg.data[3]]),
                    )[0]
                    print("alarms %d" % (alarms))
                    self.last_error_time = time.time()
                    self.error_active = True
                    self.to_protection_bits(alarms)
        return True
