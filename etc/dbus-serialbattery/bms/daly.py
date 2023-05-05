# -*- coding: utf-8 -*-
from battery import Battery, Cell
from utils import open_serial_port, logger
import utils
from struct import unpack_from
from time import sleep


class Daly(Battery):
    def __init__(self, port, baud, address):
        super(Daly, self).__init__(port, baud, address)
        self.charger_connected = None
        self.load_connected = None
        self.command_address = address
        self.cell_min_voltage = None
        self.cell_max_voltage = None
        self.cell_min_no = None
        self.cell_max_no = None
        self.poll_interval = 1000
        self.poll_step = 0
        self.type = self.BATTERYTYPE

    # command bytes [StartFlag=A5][Address=40][Command=94][DataLength=8][8x zero bytes][checksum]
    command_base = b"\xA5\x40\x94\x08\x00\x00\x00\x00\x00\x00\x00\x00\x81"
    cellvolt_buffer = b"\xA5\x40\x94\x08\x00\x00\x00\x00\x00\x00\x00\x00\x82"
    command_soc = b"\x90"
    command_minmax_cell_volts = b"\x91"
    command_minmax_temp = b"\x92"
    command_fet = b"\x93"
    command_status = b"\x94"
    command_cell_volts = b"\x95"
    command_temp = b"\x96"
    command_cell_balance = b"\x97"
    command_alarm = b"\x98"
    command_rated_params = b"\x50"
    BATTERYTYPE = "Daly"
    LENGTH_CHECK = 1
    LENGTH_POS = 3
    CURRENT_ZERO_CONSTANT = 30000
    TEMP_ZERO_CONSTANT = 40

    def test_connection(self):
        # call a function that will connect to the battery, send a command and retrieve the result.
        # The result or call should be unique to this BMS. Battery name or version, etc.
        # Return True if success, False for failure
        result = False
        try:
            ser = open_serial_port(self.port, self.baud_rate)
            if ser is not None:
                result = self.read_status_data(ser)
                self.read_soc_data(ser)
                ser.close()

        except Exception as err:
            logger.error(f"Unexpected {err=}, {type(err)=}")
            result = False

        return result

    def get_settings(self):
        self.capacity = utils.BATTERY_CAPACITY
        with open_serial_port(self.port, self.baud_rate) as ser:
            self.read_capacity(ser)

        self.max_battery_charge_current = utils.MAX_BATTERY_CHARGE_CURRENT
        self.max_battery_discharge_current = utils.MAX_BATTERY_DISCHARGE_CURRENT
        return True

    def refresh_data(self):
        result = False
        # Open serial port to be used for all data reads instead of openning multiple times
        ser = open_serial_port(self.port, self.baud_rate)
        if ser is not None:
            result = self.read_soc_data(ser)
            result = result and self.read_fed_data(ser)
            result = result and self.read_cell_voltage_range_data(ser)

            if self.poll_step == 0:
                result = result and self.read_alarm_data(ser)
                result = result and self.read_temperature_range_data(ser)
            elif self.poll_step == 1:
                result = result and self.read_cells_volts(ser)
                result = result and self.read_balance_state(ser)
                # else:          # A placeholder to remind this is the last step. Add any additional steps before here
                # This is last step so reset poll_step
                self.poll_step = -1

            self.poll_step += 1

            ser.close()

        return result

    def read_status_data(self, ser):
        status_data = self.read_serial_data_daly(ser, self.command_status)
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

        self.max_battery_voltage = utils.MAX_CELL_VOLTAGE * self.cell_count
        self.min_battery_voltage = utils.MIN_CELL_VOLTAGE * self.cell_count

        self.hardware_version = "DalyBMS " + str(self.cell_count) + " cells"
        logger.info(self.hardware_version)
        return True

    def read_soc_data(self, ser):
        # Ensure data received is valid
        crntMinValid = -(utils.MAX_BATTERY_DISCHARGE_CURRENT * 2.1)
        crntMaxValid = utils.MAX_BATTERY_CHARGE_CURRENT * 1.3
        triesValid = 2
        while triesValid > 0:
            triesValid -= 1
            soc_data = self.read_serial_data_daly(ser, self.command_soc)
            # check if connection success
            if soc_data is False:
                continue

            voltage, tmp, current, soc = unpack_from(">hhhh", soc_data)
            current = (
                (current - self.CURRENT_ZERO_CONSTANT)
                / -10
                * utils.INVERT_CURRENT_MEASUREMENT
            )
            if crntMinValid < current < crntMaxValid:
                self.voltage = voltage / 10
                self.current = current
                self.soc = soc / 10
                return True

            logger.warning("read_soc_data - triesValid " + str(triesValid))
        return False

    def read_alarm_data(self, ser):
        alarm_data = self.read_serial_data_daly(ser, self.command_alarm)
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

    def read_cells_volts(self, ser):
        if self.cell_count is not None:
            buffer = bytearray(self.cellvolt_buffer)
            buffer[1] = self.command_address[0]  # Always serial 40 or 80
            buffer[2] = self.command_cell_volts[0]

            if (int(self.cell_count) % 3) == 0:
                maxFrame = int(self.cell_count / 3)
            else:
                maxFrame = int(self.cell_count / 3) + 1
            lenFixed = (
                maxFrame * 13
            )  # 0xA5, 0x01, 0x95, 0x08 + 1 byte frame + 6 byte data + 1byte reserved + chksum

            cells_volts_data = self.read_serialport_data(
                ser, buffer, self.LENGTH_POS, 0, lenFixed
            )
            if cells_volts_data is False:
                logger.warning("read_cells_volts")
                return False

            frameCell = [0, 0, 0]
            lowMin = utils.MIN_CELL_VOLTAGE / 2
            frame = 0
            bufIdx = 0

            if len(self.cells) != self.cell_count:
                # init the numbers of cells
                self.cells = []
                for idx in range(self.cell_count):
                    self.cells.append(Cell(True))

            # logger.warning("data " + bytes(cells_volts_data).hex())

            while bufIdx <= len(cells_volts_data) - (
                4 + 8 + 1
            ):  # we at least need 13 bytes to extract the identifiers + 8 bytes payload + checksum
                b1, b2, b3, b4 = unpack_from(">BBBB", cells_volts_data, bufIdx)
                if b1 == 0xA5 and b2 == 0x01 and b3 == 0x95 and b4 == 0x08:
                    (
                        frame,
                        frameCell[0],
                        frameCell[1],
                        frameCell[2],
                        _,
                        chk,
                    ) = unpack_from(">BhhhBB", cells_volts_data, bufIdx + 4)
                    if sum(cells_volts_data[bufIdx : bufIdx + 12]) & 0xFF != chk:
                        logger.warning("bad cell voltages checksum")
                    else:
                        for idx in range(3):
                            cellnum = (
                                (frame - 1) * 3
                            ) + idx  # daly is 1 based, driver 0 based
                            if cellnum >= self.cell_count:
                                break
                            cellVoltage = frameCell[idx] / 1000
                            self.cells[cellnum].voltage = (
                                None if cellVoltage < lowMin else cellVoltage
                            )
                    bufIdx += 13  # BBBBBhhhBB -> 13 byte
                else:
                    bufIdx += 1  # step through buffer to find valid start
                    logger.warning("bad cell voltages header")
        return True

    def read_cell_voltage_range_data(self, ser):
        minmax_data = self.read_serial_data_daly(ser, self.command_minmax_cell_volts)
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

    def read_balance_state(self, ser):
        balance_data = self.read_serial_data_daly(ser, self.command_cell_balance)
        # check if connection success
        if balance_data is False:
            logger.debug("read_balance_state")
            return False

        bitdata = unpack_from(">Q", balance_data)[0]

        mask = 1 << 48
        for i in range(len(self.cells)):
            self.cells[i].balance = True if bitdata & mask else False
            mask >>= 1

    def read_temperature_range_data(self, ser):
        minmax_data = self.read_serial_data_daly(ser, self.command_minmax_temp)
        # check if connection success
        if minmax_data is False:
            logger.debug("read_temperature_range_data")
            return False

        max_temp, max_no, min_temp, min_no = unpack_from(">bbbb", minmax_data)
        self.temp1 = min_temp - self.TEMP_ZERO_CONSTANT
        self.temp2 = max_temp - self.TEMP_ZERO_CONSTANT
        return True

    def read_fed_data(self, ser):
        fed_data = self.read_serial_data_daly(ser, self.command_fet)
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

    def read_capacity(self, ser):
        capa_data = self.read_serial_data_daly(ser, self.command_rated_params)
        # check if connection success
        if capa_data is False:
            logger.warning("read_capacity")
            return False

        (capacity, cell_volt) = unpack_from(">LL", capa_data)
        self.capacity = capacity / 1000
        return True

    def generate_command(self, command):
        buffer = bytearray(self.command_base)
        buffer[1] = self.command_address[0]  # Always serial 40 or 80
        buffer[2] = command[0]
        buffer[12] = sum(buffer[:12]) & 0xFF  # checksum calc
        return buffer

    def read_serial_data_daly(self, ser, command):
        data = self.read_serialport_data(
            ser, self.generate_command(command), self.LENGTH_POS, self.LENGTH_CHECK
        )
        if data is False:
            logger.info("No reply to cmd " + bytes(command).hex())
            return False

        if len(data) <= 12:
            logger.debug("Too short reply to cmd " + bytes(command).hex())
            return False

        # search sentence start
        try:
            idx = data.index(0xA5)
        except ValueError:
            logger.debug(
                "No Sentence Start found for reply to cmd " + bytes(command).hex()
            )
            return False

        if len(data[idx:]) <= 12:
            logger.debug("Too short reply to cmd " + bytes(command).hex())
            return False

        if data[12 + idx] != sum(data[idx : 12 + idx]) & 0xFF:
            logger.debug("Bad checksum in reply to cmd " + bytes(command).hex())
            return False

        _, _, _, length = unpack_from(">BBBB", data, idx)

        if length == 8:
            return data[4 + idx : length + 4 + idx]
        else:
            logger.debug(
                ">>> ERROR: Incorrect Reply to CMD "
                + bytes(command).hex()
                + ": 0x"
                + bytes(data).hex()
            )
            return False

    # Read data from previously openned serial port
    def read_serialport_data(
        self,
        ser,
        command,
        length_pos,
        length_check,
        length_fixed=None,
        length_size=None,
    ):
        try:
            ser.flushOutput()
            ser.flushInput()
            ser.write(command)

            length_byte_size = 1
            if length_size is not None:
                if length_size.upper() == "H":
                    length_byte_size = 2
                elif length_size.upper() == "I" or length_size.upper() == "L":
                    length_byte_size = 4

            count = 0
            toread = ser.inWaiting()

            while toread < (length_pos + length_byte_size):
                sleep(0.005)
                toread = ser.inWaiting()
                count += 1
                if count > 50:
                    logger.error(">>> ERROR: No reply - returning")
                    return False

            # logger.info('serial data toread ' + str(toread))
            res = ser.read(toread)
            if length_fixed is not None:
                length = length_fixed
            else:
                if len(res) < (length_pos + length_byte_size):
                    logger.error(
                        ">>> ERROR: No reply - returning [len:" + str(len(res)) + "]"
                    )
                    return False
                length_size = length_size if length_size is not None else "B"
                length = unpack_from(">" + length_size, res, length_pos)[0]

            # logger.info('serial data length ' + str(length))

            count = 0
            data = bytearray(res)

            packetlen = (
                length_fixed
                if length_fixed is not None
                else length_pos + length_byte_size + length + length_check
            )
            while len(data) < packetlen:
                res = ser.read(packetlen - len(data))
                data.extend(res)
                # logger.info('serial data length ' + str(len(data)))
                sleep(0.005)
                count += 1
                if count > 150:
                    logger.error(
                        ">>> ERROR: No reply - returning [len:"
                        + str(len(data))
                        + "/"
                        + str(length + length_check)
                        + "]"
                    )
                    return False

            return data

        except Exception as e:
            logger.error(e)
            return False
