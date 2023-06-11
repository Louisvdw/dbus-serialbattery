# -*- coding: utf-8 -*-
from battery import Battery, Cell
from utils import open_serial_port, logger
import utils
from struct import unpack_from, pack_into
from time import sleep, time
from datetime import datetime
from re import sub


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
        self.type = self.BATTERYTYPE
        self.has_settings = 1
        self.reset_soc = 0
        self.soc_to_set = None
        self.runtime = 0  # TROUBLESHOOTING for no reply errors
        self.trigger_force_disable_discharge = None
        self.trigger_force_disable_charge = None
        self.cells_volts_data_lastreadbad = False

    # command bytes [StartFlag=A5][Address=40][Command=94][DataLength=8][8x zero bytes][checksum]
    command_base = b"\xA5\x40\x94\x08\x00\x00\x00\x00\x00\x00\x00\x00\x81"
    command_set_soc = b"\x21"
    command_rated_params = b"\x50"
    command_batt_details = b"\x53"
    command_batt_code = b"\x57"
    command_soc = b"\x90"
    command_minmax_cell_volts = b"\x91"  # no reply
    command_minmax_temp = b"\x92"  # no reply
    command_fet = b"\x93"  # no reply
    command_status = b"\x94"
    command_cell_volts = b"\x95"
    command_temp = b"\x96"
    command_cell_balance = b"\x97"  # no reply
    command_alarm = b"\x98"  # no reply
    command_disable_discharge_mos = b"\xD9"
    command_disable_charge_mos = b"\xDA"

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
            with open_serial_port(self.port, self.baud_rate) as ser:
                result = self.read_status_data(ser)
                # get first data to show in startup log, only if result is true
                if result:
                    self.read_soc_data(ser)
                    self.read_battery_code(ser)

        except Exception as err:
            logger.error(f"Unexpected {err=}, {type(err)=}")
            result = False

        # give the user a feedback that no BMS was found
        if not result:
            logger.error(">>> ERROR: No reply - returning")

        return result

    def get_settings(self):
        self.capacity = utils.BATTERY_CAPACITY
        with open_serial_port(self.port, self.baud_rate) as ser:
            self.read_capacity(ser)
            self.read_production_date(ser)

        self.max_battery_charge_current = utils.MAX_BATTERY_CHARGE_CURRENT
        self.max_battery_discharge_current = utils.MAX_BATTERY_DISCHARGE_CURRENT
        return True

    def refresh_data(self):
        result = False

        # Open serial port to be used for all data reads instead of opening multiple times
        try:
            with open_serial_port(self.port, self.baud_rate) as ser:
                result = self.read_soc_data(ser)
                self.reset_soc = self.soc if self.soc else 0
                if self.runtime > 0.200:  # TROUBLESHOOTING for no reply errors
                    logger.info(
                        "  |- refresh_data: read_soc_data - result: "
                        + str(result)
                        + " - runtime: "
                        + str(f"{self.runtime:.1f}")
                        + "s"
                    )

                result = self.read_fed_data(ser) and result
                if self.runtime > 0.200:  # TROUBLESHOOTING for no reply errors
                    logger.info(
                        "  |- refresh_data: read_fed_data - result: "
                        + str(result)
                        + " - runtime: "
                        + str(f"{self.runtime:.1f}")
                        + "s"
                    )

                result = self.read_cell_voltage_range_data(ser) and result
                if self.runtime > 0.200:  # TROUBLESHOOTING for no reply errors
                    logger.info(
                        "  |- refresh_data: read_cell_voltage_range_data - result: "
                        + str(result)
                        + " - runtime: "
                        + str(f"{self.runtime:.1f}")
                        + "s"
                    )

                self.write_soc_and_datetime(ser)
                if self.runtime > 0.200:  # TROUBLESHOOTING for no reply errors
                    logger.info(
                        "  |- refresh_data: write_soc_and_datetime - result: "
                        + str(result)
                        + " - runtime: "
                        + str(f"{self.runtime:.1f}")
                        + "s"
                    )

                result = self.read_alarm_data(ser) and result
                if self.runtime > 0.200:  # TROUBLESHOOTING for no reply errors
                    logger.info(
                        "  |- refresh_data: read_alarm_data - result: "
                        + str(result)
                        + " - runtime: "
                        + str(f"{self.runtime:.1f}")
                        + "s"
                    )

                result = self.read_temperature_range_data(ser) and result
                if self.runtime > 0.200:  # TROUBLESHOOTING for no reply errors
                    logger.info(
                        "  |- refresh_data: read_temperature_range_data - result: "
                        + str(result)
                        + " - runtime: "
                        + str(f"{self.runtime:.1f}")
                        + "s"
                    )

                result = self.read_balance_state(ser) and result
                if self.runtime > 0.200:  # TROUBLESHOOTING for no reply errors
                    logger.info(
                        "  |- refresh_data: read_balance_state - result: "
                        + str(result)
                        + " - runtime: "
                        + str(f"{self.runtime:.1f}")
                        + "s"
                    )

                result = self.read_cells_volts(ser) and result
                if self.runtime > 0.200:  # TROUBLESHOOTING for no reply errors
                    logger.info(
                        "  |- refresh_data: read_cells_volts - result: "
                        + str(result)
                        + " - runtime: "
                        + str(f"{self.runtime:.1f}")
                        + "s"
                    )

                self.write_charge_discharge_mos(ser)

        except OSError:
            logger.warning("Couldn't open serial port")

        if not result:  # TROUBLESHOOTING for no reply errors
            logger.info("refresh_data: result: " + str(result))
        return result

    def read_status_data(self, ser):
        status_data = self.request_data(ser, self.command_status)
        # check if connection success
        if status_data is False:
            logger.debug("No data received in read_status_data()")
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

        self.hardware_version = (
            "DalyBMS "
            + str(self.cell_count)
            + " cells"
            + (" (" + self.production + ")" if self.production else "")
        )
        logger.debug(self.hardware_version)
        return True

    def read_soc_data(self, ser):
        # Ensure data received is valid
        crntMinValid = -(utils.MAX_BATTERY_DISCHARGE_CURRENT * 2.1)
        crntMaxValid = utils.MAX_BATTERY_CHARGE_CURRENT * 1.3
        triesValid = 2
        while triesValid > 0:
            triesValid -= 1
            soc_data = self.request_data(ser, self.command_soc)
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
        alarm_data = self.request_data(ser, self.command_alarm)
        # check if connection success
        if alarm_data is False:
            logger.warning("No data received in read_alarm_data()")
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
            self.protection.voltage_high = 2
        elif al_volt & 15:
            # High voltage Warning levels - Pre-alarm
            self.protection.voltage_high = 1
        else:
            self.protection.voltage_high = 0

        if al_volt & 128:
            # Low voltage level - Alarm
            self.protection.voltage_low = 2
        elif al_volt & 64:
            # Low voltage Warning level - Pre-alarm
            self.protection.voltage_low = 1
        else:
            self.protection.voltage_low = 0

        if al_temp & 2:
            # High charge temp - Alarm
            self.protection.temp_high_charge = 2
        elif al_temp & 1:
            # High charge temp - Pre-alarm
            self.protection.temp_high_charge = 1
        else:
            self.protection.temp_high_charge = 0

        if al_temp & 8:
            # Low charge temp - Alarm
            self.protection.temp_low_charge = 2
        elif al_temp & 4:
            # Low charge temp - Pre-alarm
            self.protection.temp_low_charge = 1
        else:
            self.protection.temp_low_charge = 0

        if al_temp & 32:
            # High discharge temp - Alarm
            self.protection.temp_high_discharge = 2
        elif al_temp & 16:
            # High discharge temp - Pre-alarm
            self.protection.temp_high_discharge = 1
        else:
            self.protection.temp_high_discharge = 0

        if al_temp & 128:
            # Low discharge temp - Alarm
            self.protection.temp_low_discharge = 2
        elif al_temp & 64:
            # Low discharge temp - Pre-alarm
            self.protection.temp_low_discharge = 1
        else:
            self.protection.temp_low_discharge = 0

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
            self.protection.current_over = 2
        elif al_crnt_soc & 1 or al_crnt_soc & 4:
            # High charge/discharge current - Pre-alarm
            self.protection.current_over = 1
        else:
            self.protection.current_over = 0

        if al_crnt_soc & 128:
            # Low SoC - Alarm
            self.protection.soc_low = 2
        elif al_crnt_soc & 64:
            # Low SoC Warning level - Pre-alarm
            self.protection.soc_low = 1
        else:
            self.protection.soc_low = 0

        return True

    def read_cells_volts(self, ser):
        if self.cell_count is None:
            return True

        # calculate how many sentences we will receive
        # in each sentence, the bms will send 3 cell voltages
        # so for a 4s, we will receive 2 sentences
        if (int(self.cell_count) % 3) == 0:
            sentences_expected = int(self.cell_count / 3)
        else:
            sentences_expected = int(self.cell_count / 3) + 1

        cells_volts_data = self.request_data(
            ser, self.command_cell_volts, sentences_to_receive=sentences_expected
        )

        if cells_volts_data is False and self.cells_volts_data_lastreadbad is True:
            # if this read out and the last one were bad, report error.
            # (we don't report single errors, as current daly firmware sends corrupted cells volts data occassionally)
            logger.debug(
                "No or invalid data has been received repeatedly in read_cells_volts()"
            )
            return False
        elif cells_volts_data is False:
            # memorize that this read was bad and bail out, ignoring it
            self.cells_volts_data_lastreadbad = True
            return True
        else:
            # this read was good, so reset error flag
            self.cells_volts_data_lastreadbad = False

        frameCell = [0, 0, 0]
        lowMin = utils.MIN_CELL_VOLTAGE / 2
        frame = 0

        if len(self.cells) != self.cell_count:
            # init the numbers of cells
            self.cells = []
            for idx in range(self.cell_count):
                self.cells.append(Cell(True))

        # logger.warning("data " + bytes(cells_volts_data).hex())

        # from each of the received sentences, read up to 3 voltages
        for i in range(sentences_expected):
            (
                frame,
                frameCell[0],
                frameCell[1],
                frameCell[2],
            ) = unpack_from(">Bhhh", cells_volts_data, 8 * i)
            for idx in range(3):
                cellnum = ((frame - 1) * 3) + idx  # daly is 1 based, driver 0 based
                if cellnum >= self.cell_count:
                    break  # ignore possible unused bytes of last sentence
                cellVoltage = frameCell[idx] / 1000
                self.cells[cellnum].voltage = (
                    None if cellVoltage < lowMin else cellVoltage
                )
        return True

    def read_cell_voltage_range_data(self, ser):
        minmax_data = self.request_data(ser, self.command_minmax_cell_volts)
        # check if connection success
        if minmax_data is False:
            logger.debug("No data received in read_cell_voltage_range_data()")
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
        balance_data = self.request_data(ser, self.command_cell_balance)
        # check if connection success
        if balance_data is False:
            logger.debug("No data received in read_balance_state()")
            return False

        bitdata = unpack_from(">Q", balance_data)[0]

        mask = 1 << 48
        for i in range(len(self.cells)):
            self.cells[i].balance = True if bitdata & mask else False
            mask >>= 1

        return True

    def read_temperature_range_data(self, ser):
        minmax_data = self.request_data(ser, self.command_minmax_temp)
        # check if connection success
        if minmax_data is False:
            logger.debug("No data received in read_temperature_range_data()")
            return False

        max_temp, max_no, min_temp, min_no = unpack_from(">bbbb", minmax_data)
        self.temp1 = min_temp - self.TEMP_ZERO_CONSTANT
        self.temp2 = max_temp - self.TEMP_ZERO_CONSTANT
        return True

    def read_fed_data(self, ser):
        fed_data = self.request_data(ser, self.command_fet)
        # check if connection success
        if fed_data is False:
            logger.debug("No data received in read_fed_data()")
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

    # new
    def read_capacity(self, ser):
        capa_data = self.request_data(ser, self.command_rated_params)
        # check if connection success
        if capa_data is False:
            logger.debug("No data received in read_capacity()")
            return False

        (capacity, cell_volt) = unpack_from(">LL", capa_data)
        if capacity and capacity > 0:
            self.capacity = capacity / 1000
            return True
        else:
            return False

    # new
    def read_production_date(self, ser):
        production = self.request_data(ser, self.command_batt_details)
        # check if connection success
        if production is False:
            logger.debug("No data received in read_production_date()")
            return False

        (_, _, year, month, day) = unpack_from(">BBBBB", production)
        self.production = f"{year + 2000}{month:02d}{day:02d}"
        return True

    # new
    def read_battery_code(self, ser):
        data = self.request_data(ser, self.command_batt_code, sentences_to_receive=5)

        if data is False:
            logger.debug("No data received in read_battery_code()")
            return False

        battery_code = ""
        # logger.warning("data " + bytes(cells_volts_data).hex())
        for i in range(5):
            nr, part = unpack_from(">B7s", data, i * 8)
            if nr != i + 1:
                logger.debug("bad battery code index")  # use string anyhow, just warn
            battery_code += part.decode("utf-8")

        if battery_code != "":
            self.custom_field = sub(
                " +",
                " ",
                (battery_code.strip()),
            )
        return True

    def unique_identifier(self) -> str:
        """
        Used to identify a BMS when multiple BMS are connected
        """
        if self.custom_field != "":
            return self.custom_field.replace(" ", "_")
        else:
            return str(self.production) + "_" + str(int(self.capacity))

    def reset_soc_callback(self, path, value):
        if value is None:
            return False

        if value < 0 or value > 100:
            return False

        self.reset_soc = value
        self.soc_to_set = value
        return True

    def write_soc_and_datetime(self, ser):
        if self.soc_to_set is None:
            return False

        cmd = bytearray(13)
        now = datetime.now()

        pack_into(
            ">BBBBBBBBBBH",
            cmd,
            0,
            0xA5,
            self.command_address[0],
            self.command_set_soc[0],
            8,
            now.year - 2000,
            now.month,
            now.day,
            now.hour,
            now.minute,
            now.second,
            int(self.soc_to_set * 10),
        )
        cmd[12] = sum(cmd[:12]) & 0xFF

        logger.info(f"write soc {self.soc_to_set}%")
        self.soc_to_set = None  # Reset value, so we will set it only once

        ser.flushOutput()
        ser.flushInput()
        ser.write(cmd)

        reply = self.read_sentence(ser, self.command_set_soc)
        if reply is False or reply[0] != 1:
            logger.error("write soc failed")
        return True

    def force_charging_off_callback(self, path, value):
        if value is None:
            return False

        if value == 0:
            self.trigger_force_disable_charge = False
            return True

        if value == 1:
            self.trigger_force_disable_charge = True
            return True

        return False

    def force_discharging_off_callback(self, path, value):
        if value is None:
            return False

        if value == 0:
            self.trigger_force_disable_discharge = False
            return True

        if value == 1:
            self.trigger_force_disable_discharge = True
            return True

        return False

    def write_charge_discharge_mos(self, ser):
        if (
            self.trigger_force_disable_charge is None
            and self.trigger_force_disable_discharge is None
        ):
            return False

        cmd = bytearray(self.command_base)

        if self.trigger_force_disable_charge is not None:
            cmd[2] = self.command_disable_charge_mos[0]
            cmd[4] = 0 if self.trigger_force_disable_charge else 1
            cmd[12] = sum(cmd[:12]) & 0xFF
            logger.info(
                f"write force disable charging: {'true' if self.trigger_force_disable_charge else 'false'}"
            )
            self.trigger_force_disable_charge = None
            ser.flushOutput()
            ser.flushInput()
            ser.write(cmd)

            reply = self.read_sentence(ser, self.command_disable_charge_mos)
            if reply is False or reply[0] != cmd[4]:
                logger.error("write force disable charge/discharge failed")
                return False

        if self.trigger_force_disable_discharge is not None:
            cmd[2] = self.command_disable_discharge_mos[0]
            cmd[4] = 0 if self.trigger_force_disable_discharge else 1
            cmd[12] = sum(cmd[:12]) & 0xFF
            logger.info(
                f"write force disable discharging: {'true' if self.trigger_force_disable_discharge else 'false'}"
            )
            self.trigger_force_disable_discharge = None
            ser.flushOutput()
            ser.flushInput()
            ser.write(cmd)

            reply = self.read_sentence(ser, self.command_disable_discharge_mos)
            if reply is False or reply[0] != cmd[4]:
                logger.error("write force disable charge/discharge failed")
                return False
        return True

    def generate_command(self, command):
        buffer = bytearray(self.command_base)
        buffer[1] = self.command_address[0]  # Always serial 40 or 80
        buffer[2] = command[0]
        buffer[12] = sum(buffer[:12]) & 0xFF  # checksum calc
        return buffer

    def request_data(self, ser, command, sentences_to_receive=1):
        # wait shortly, else the Daly is not ready and throws a lot of no reply errors
        # if you see a lot of errors, try to increase in steps of 0.005
        sleep(0.020)

        self.runtime = 0
        time_start = time()
        ser.flushOutput()
        ser.flushInput()
        ser.write(self.generate_command(command))

        reply = bytearray()
        for i in range(sentences_to_receive):
            next = self.read_sentence(ser, command)
            if not next:
                logger.debug(f"request_data: bad reply no. {i}")
                return False
            reply += next
        self.runtime = time() - time_start
        return reply

    def read_sentence(self, ser, expected_reply, timeout=0.5):
        """read one 13 byte sentence from daly smart bms.
        return false if less than 13 bytes received in timeout secs, or frame errors occured
        return received datasection as bytearray else
        """
        time_start = time()

        reply = ser.read_until(b"\xA5")
        if not reply or b"\xA5" not in reply:
            logger.debug(
                f"read_sentence {bytes(expected_reply).hex()}: no sentence start received"
            )
            return False

        idx = reply.index(b"\xA5")
        reply = reply[idx:]
        toread = ser.inWaiting()
        while toread < 12:
            sleep((12 - toread) * 0.001)
            toread = ser.inWaiting()
            time_run = time() - time_start
            if time_run > timeout:
                logger.debug(f"read_sentence {bytes(expected_reply).hex()}: timeout")
                return False

        reply += ser.read(12)
        _, id, cmd, length = unpack_from(">BBBB", reply)

        # logger.info(f"reply: {bytes(reply).hex()}")  # debug

        if id != 1 or length != 8 or cmd != expected_reply[0]:
            logger.debug(f"read_sentence {bytes(expected_reply).hex()}: wrong header")
            return False

        chk = unpack_from(">B", reply, 12)[0]
        if sum(reply[:12]) & 0xFF != chk:
            logger.debug(f"read_sentence {bytes(expected_reply).hex()}: wrong checksum")
            return False

        return reply[4:12]
