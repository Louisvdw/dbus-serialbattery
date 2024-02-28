# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from battery import Battery, Cell
from utils import (
    BATTERY_CAPACITY,
    INVERT_CURRENT_MEASUREMENT,
    logger,
    MAX_BATTERY_CHARGE_CURRENT,
    MAX_BATTERY_DISCHARGE_CURRENT,
    MAX_CELL_VOLTAGE,
    MIN_CELL_VOLTAGE,
)
from struct import unpack_from
import can

"""
https://github.com/Louisvdw/dbus-serialbattery/pull/169
"""


class Daly_Can(Battery):
    def __init__(self, port, baud, address):
        super(Daly_Can, self).__init__(port, baud, address)
        self.charger_connected = None
        self.load_connected = None
        self.cell_min_voltage = None
        self.cell_max_voltage = None
        self.cell_min_no = None
        self.cell_max_no = None
        self.poll_interval = 1000
        self.poll_step = 0
        self.type = self.BATTERYTYPE
        self.can_bus = None

    # command bytes [Priority=18][Command=94][BMS ID=01][Uplink ID=40]
    command_base = 0x18940140
    command_soc = 0x18900140
    command_minmax_cell_volts = 0x18910140
    command_minmax_temp = 0x18920140
    command_fet = 0x18930140
    command_status = 0x18940140
    command_cell_volts = 0x18950140
    command_temp = 0x18960140
    command_cell_balance = 0x18970140
    command_alarm = 0x18980140

    response_base = 0x18944001
    response_soc = 0x18904001
    response_minmax_cell_volts = 0x18914001
    response_minmax_temp = 0x18924001
    response_fet = 0x18934001
    response_status = 0x18944001
    response_cell_volts = 0x18954001
    response_temp = 0x18964001
    response_cell_balance = 0x18974001
    response_alarm = 0x18984001

    BATTERYTYPE = "Daly_Can"
    LENGTH_CHECK = 4
    LENGTH_POS = 3
    CURRENT_ZERO_CONSTANT = 30000
    TEMP_ZERO_CONSTANT = 40

    def test_connection(self):
        result = False

        # TODO handle errors?
        can_filters = [
            {"can_id": self.response_base, "can_mask": 0xFFFFFFF},
            {"can_id": self.response_soc, "can_mask": 0xFFFFFFF},
            {"can_id": self.response_minmax_cell_volts, "can_mask": 0xFFFFFFF},
            {"can_id": self.response_minmax_temp, "can_mask": 0xFFFFFFF},
            {"can_id": self.response_fet, "can_mask": 0xFFFFFFF},
            {"can_id": self.response_status, "can_mask": 0xFFFFFFF},
            {"can_id": self.response_cell_volts, "can_mask": 0xFFFFFFF},
            {"can_id": self.response_temp, "can_mask": 0xFFFFFFF},
            {"can_id": self.response_cell_balance, "can_mask": 0xFFFFFFF},
            {"can_id": self.response_alarm, "can_mask": 0xFFFFFFF},
        ]
        self.can_bus = can.Bus(
            interface="socketcan",
            channel=self.port,
            receive_own_messages=False,
            can_filters=can_filters,
        )

        result = self.read_status_data(self.can_bus)

        return result

    def get_settings(self):
        self.capacity = BATTERY_CAPACITY
        self.max_battery_charge_current = MAX_BATTERY_CHARGE_CURRENT
        self.max_battery_discharge_current = MAX_BATTERY_DISCHARGE_CURRENT
        return True

    def refresh_data(self):
        result = False

        result = self.read_soc_data(self.can_bus)
        result = result and self.read_fed_data(self.can_bus)
        if self.poll_step == 0:
            # This must be listed in step 0 as get_min_cell_voltage and get_max_cell_voltage in battery.py
            # needs it at first cycle for publish_dbus in dbushelper.py
            result = result and self.read_cell_voltage_range_data(self.can_bus)
        elif self.poll_step == 1:
            result = result and self.read_alarm_data(self.can_bus)
        elif self.poll_step == 2:
            result = result and self.read_cells_volts(self.can_bus)
        elif self.poll_step == 3:
            result = result and self.read_temperature_range_data(self.can_bus)
            # else:          # A placeholder to remind this is the last step. Add any additional steps before here
            # This is last step so reset poll_step
            self.poll_step = -1

        self.poll_step += 1

        return result

    def read_status_data(self, can_bus):
        status_data = self.read_bus_data_daly(can_bus, self.command_status)
        # check if connection success
        if status_data is False:
            logger.debug("read_status_data")
            return False

        (
            self.cell_count,
            self.temp_sensors,
            self.charger_connected,
            self.load_connected,
            state,
            self.cycles,
        ) = unpack_from(">bb??bhx", status_data)

        self.max_battery_voltage = MAX_CELL_VOLTAGE * self.cell_count
        self.min_battery_voltage = MIN_CELL_VOLTAGE * self.cell_count

        self.hardware_version = "DalyBMS " + str(self.cell_count) + " cells"
        logger.info(self.hardware_version)
        return True

    def read_soc_data(self, ser):
        # Ensure data received is valid
        crntMinValid = -(MAX_BATTERY_DISCHARGE_CURRENT * 2.1)
        crntMaxValid = MAX_BATTERY_CHARGE_CURRENT * 1.3
        triesValid = 2
        while triesValid > 0:
            soc_data = self.read_bus_data_daly(ser, self.command_soc)
            # check if connection success
            if soc_data is False:
                return False

            voltage, tmp, current, soc = unpack_from(">hhhh", soc_data)
            current = (
                (current - self.CURRENT_ZERO_CONSTANT)
                / -10
                * INVERT_CURRENT_MEASUREMENT
            )
            # logger.info("voltage: " + str(voltage) + ", current: " + str(current) + ", soc: " + str(soc))
            if crntMinValid < current < crntMaxValid:
                self.voltage = voltage / 10
                self.current = current
                self.soc = soc / 10
                return True

            logger.warning("read_soc_data - triesValid " + str(triesValid))
            triesValid -= 1

        return False

    def read_alarm_data(self, ser):
        alarm_data = self.read_bus_data_daly(ser, self.command_alarm)
        # check if connection success
        if alarm_data is False:
            logger.warning("read_alarm_data")
            return False

        (
            al_volt,
            al_temp,
            al_crnt_soc,
            al_diff,
            al_mos,
            al_misc1,
            al_misc2,
            al_fault,
        ) = unpack_from(">bbbbbbbb", alarm_data)

        if al_volt & 48:
            # High voltage levels - Alarm
            self.voltage_high = 2
        elif al_volt & 15:
            # High voltage Warning levels - Pre-alarm
            self.voltage_high = 1
        else:
            self.voltage_high = 0

        if al_volt & 128:
            # Low voltage level - Alarm
            self.voltage_low = 2
        elif al_volt & 64:
            # Low voltage Warning level - Pre-alarm
            self.voltage_low = 1
        else:
            self.voltage_low = 0

        if al_temp & 2:
            # High charge temp - Alarm
            self.temp_high_charge = 2
        elif al_temp & 1:
            # High charge temp - Pre-alarm
            self.temp_high_charge = 1
        else:
            self.temp_high_charge = 0

        if al_temp & 8:
            # Low charge temp - Alarm
            self.temp_low_charge = 2
        elif al_temp & 4:
            # Low charge temp - Pre-alarm
            self.temp_low_charge = 1
        else:
            self.temp_low_charge = 0

        if al_temp & 32:
            # High discharge temp - Alarm
            self.temp_high_discharge = 2
        elif al_temp & 16:
            # High discharge temp - Pre-alarm
            self.temp_high_discharge = 1
        else:
            self.temp_high_discharge = 0

        if al_temp & 128:
            # Low discharge temp - Alarm
            self.temp_low_discharge = 2
        elif al_temp & 64:
            # Low discharge temp - Pre-alarm
            self.temp_low_discharge = 1
        else:
            self.temp_low_discharge = 0

        # if al_crnt_soc & 2:
        #    # High charge current - Alarm
        #    self.current_over = 2
        # elif al_crnt_soc & 1:
        #    # High charge current - Pre-alarm
        #    self.current_over = 1
        # else:
        #    self.current_over = 0

        # if al_crnt_soc & 8:
        #    # High discharge current - Alarm
        #    self.current_over = 2
        # elif al_crnt_soc & 4:
        #    # High discharge current - Pre-alarm
        #    self.current_over = 1
        # else:
        #    self.current_over = 0

        if al_crnt_soc & 2 or al_crnt_soc & 8:
            # High charge/discharge current - Alarm
            self.current_over = 2
        elif al_crnt_soc & 1 or al_crnt_soc & 4:
            # High charge/discharge current - Pre-alarm
            self.current_over = 1
        else:
            self.current_over = 0

        if al_crnt_soc & 128:
            # Low SoC - Alarm
            self.soc_low = 2
        elif al_crnt_soc & 64:
            # Low SoC Warning level - Pre-alarm
            self.soc_low = 1
        else:
            self.soc_low = 0

        return True

    def read_cells_volts(self, can_bus):
        if self.cell_count is not None:
            cells_volts_data = self.read_bus_data_daly(
                can_bus, self.command_cell_volts, 6
            )
            if cells_volts_data is False:
                logger.warning("read_cells_volts")
                return False

            frameCell = [0, 0, 0]
            lowMin = MIN_CELL_VOLTAGE / 2
            frame = 0
            bufIdx = 0

            if len(self.cells) != self.cell_count:
                # init the numbers of cells
                self.cells = []
                for idx in range(self.cell_count):
                    self.cells.append(Cell(True))

            while bufIdx < len(cells_volts_data):
                frame, frameCell[0], frameCell[1], frameCell[2] = unpack_from(
                    ">Bhhh", cells_volts_data, bufIdx
                )
                for idx in range(3):
                    cellnum = ((frame - 1) * 3) + idx  # daly is 1 based, driver 0 based
                    if cellnum >= self.cell_count:
                        break
                    cellVoltage = frameCell[idx] / 1000
                    self.cells[cellnum].voltage = (
                        None if cellVoltage < lowMin else cellVoltage
                    )
                bufIdx += 8

        return True

    def read_cell_voltage_range_data(self, ser):
        minmax_data = self.read_bus_data_daly(ser, self.command_minmax_cell_volts)
        # check if connection success
        if minmax_data is False:
            logger.warning("read_cell_voltage_range_data")
            return False

        (
            cell_max_voltage,
            self.cell_max_no,
            cell_min_voltage,
            self.cell_min_no,
        ) = unpack_from(">hbhb", minmax_data)
        # Daly cells numbers are 1 based and not 0 based
        self.cell_min_no -= 1
        self.cell_max_no -= 1
        # Voltage is returned in mV
        self.cell_max_voltage = cell_max_voltage / 1000
        self.cell_min_voltage = cell_min_voltage / 1000
        return True

    def read_temperature_range_data(self, ser):
        minmax_data = self.read_bus_data_daly(ser, self.command_minmax_temp)
        # check if connection success
        if minmax_data is False:
            logger.debug("read_temperature_range_data")
            return False

        max_temp, max_no, min_temp, min_no = unpack_from(">bbbb", minmax_data)
        self.temp1 = min_temp - self.TEMP_ZERO_CONSTANT
        self.temp2 = max_temp - self.TEMP_ZERO_CONSTANT
        return True

    def read_fed_data(self, ser):
        fed_data = self.read_bus_data_daly(ser, self.command_fet)
        # check if connection success
        if fed_data is False:
            logger.debug("read_fed_data")
            return False

        (
            status,
            self.charge_fet,
            self.discharge_fet,
            bms_cycles,
            capacity_remain,
        ) = unpack_from(">b??BL", fed_data)
        self.capacity_remain = capacity_remain / 1000
        return True

    def read_bus_data_daly(self, can_bus, command, expectedMessageCount=1):
        # TODO handling of error cases
        message = can.Message(arbitration_id=command)
        can_bus.send(message, timeout=0.2)
        response = bytearray()

        # TODO use async notifier instead of this where we expect a specific frame to be received
        # this could end up in a deadlock if a package is not received
        count = 0
        for msg in can_bus:
            # print(f"{msg.arbitration_id:X}: {msg.data}")
            # logger.info('Frame: ' + ", ".join(hex(b) for b in msg.data))
            response.extend(msg.data)
            count += 1
            if count == expectedMessageCount:
                break
        return response
