# -*- coding: utf-8 -*-
from battery import Protection, Battery, Cell
from utils import is_bit_set, read_serial_data, logger
import utils
from struct import unpack_from
import struct

# Protocol registers
REG_ENTER_FACTORY = 0x00
REG_EXIT_FACTORY = 0x01
# REG_UNKNOWN = 0x02
REG_GENERAL = 0x03
REG_CELL = 0x04
REG_HARDWARE = 0x05
# Firmware 0x16+
REG_USE_PASSWORD = 0x06
REG_SET_PASSWORD = 0x07
# REG_UNKNOWN2 = 0x08 - Maybe define master password?
REG_CLEAR_PASSWORD = 0x09

REG_FRESET = 0x0A

REG_DESIGN_CAP = 0x10
REG_CYCLE_CAP = 0x11
REG_CAP_100 = 0x12
REG_CAP_0 = 0x13
REG_SELF_DSG_RATE = 0x14
REG_MFG_DATE = 0x15
REG_SERIAL_NUM = 0x16
REG_CYCLE_CNT = 0x17
REG_CHGOT = 0x18
REG_CHGOT_REL = 0x19
REG_CHGUT = 0x1A
REG_CHGUT_REL = 0x1B
REG_DSGOT = 0x1C
REG_DSGOT_REL = 0x1D
REG_DSGUT = 0x1E
REG_DSGUT_REL = 0x1F
REG_POVP = 0x20
REG_POVP_REL = 0x21
REG_PUVP = 0x22
REG_PUVP_REL = 0x23
REG_COVP = 0x24
REG_COVP_REL = 0x25
REG_CUVP = 0x26
REG_CUVP_REL = 0x27
REG_CHGOC = 0x28
REG_DSGOC = 0x29
REG_BAL_START = 0x2A
REG_BAL_WINDOW = 0x2B
REG_SHUNT_RES = 0x2C
REG_FUNC_CONFIG = 0x2D
REG_NTC_CONFIG = 0x2E
REG_CELL_CNT = 0x2F
REG_FET_TIME = 0x30
REG_LED_TIME = 0x31
REG_CAP_80 = 0x32
REG_CAP_60 = 0x33
REG_CAP_40 = 0x34
REG_CAP_20 = 0x35
REG_COVP_HIGH = 0x36
REG_CUVP_HIGH = 0x37
REG_SC_DSGOC2 = 0x38
REG_CXVP_HIGH_DELAY_SC_REL = 0x39
REG_CHG_T_DELAYS = 0x3A
REG_DSG_T_DELAYS = 0x3B
REG_PACK_V_DELAYS = 0x3C
REG_CELL_V_DELAYS = 0x3D
REG_CHGOC_DELAYS = 0x3E
REG_DSGOC_DELAYS = 0x3F
REG_GPSOFF = 0x40
REG_GPSOFF_TIME = 0x41
REG_CAP_90 = 0x42
REG_CAP_70 = 0x43
REG_CAP_50 = 0x44
REG_CAP_30 = 0x45
REG_CAP_10 = 0x46
# REG_CAP2_100 = 0x47

# [0x48, 0x9F] - 87 registers

REG_MFGNAME = 0xA0
REG_MODEL = 0xA1
REG_BARCODE = 0xA2
REG_ERROR = 0xAA
# 0xAB
# 0xAC
REG_CAL_CUR_IDLE = 0xAD
REG_CAL_CUR_CHG = 0xAE
REG_CAL_CUR_DSG = 0xAF

REG_CAL_V_CELL_01 = 0xB0
REG_CAL_V_CELL_02 = 0xB1
REG_CAL_V_CELL_03 = 0xB2
REG_CAL_V_CELL_04 = 0xB3
REG_CAL_V_CELL_05 = 0xB4
REG_CAL_V_CELL_06 = 0xB5
REG_CAL_V_CELL_07 = 0xB6
REG_CAL_V_CELL_08 = 0xB7
REG_CAL_V_CELL_09 = 0xB8
REG_CAL_V_CELL_10 = 0xB9
REG_CAL_V_CELL_11 = 0xBA
REG_CAL_V_CELL_12 = 0xBB
REG_CAL_V_CELL_13 = 0xBC
REG_CAL_V_CELL_14 = 0xBD
REG_CAL_V_CELL_15 = 0xBE
REG_CAL_V_CELL_16 = 0xBF
REG_CAL_V_CELL_17 = 0xC0
REG_CAL_V_CELL_18 = 0xC1
REG_CAL_V_CELL_19 = 0xC2
REG_CAL_V_CELL_20 = 0xC3
REG_CAL_V_CELL_21 = 0xC4
REG_CAL_V_CELL_22 = 0xC5
REG_CAL_V_CELL_23 = 0xC6
REG_CAL_V_CELL_24 = 0xC7
REG_CAL_V_CELL_25 = 0xC8
REG_CAL_V_CELL_26 = 0xC9
REG_CAL_V_CELL_27 = 0xCA
REG_CAL_V_CELL_28 = 0xCB
REG_CAL_V_CELL_29 = 0xCC
REG_CAL_V_CELL_30 = 0xCD
REG_CAL_V_CELL_31 = 0xCE
REG_CAL_V_CELL_32 = 0xCF

REG_CAL_T_NTC_0 = 0xD0
REG_CAL_T_NTC_1 = 0xD1
REG_CAL_T_NTC_2 = 0xD2
REG_CAL_T_NTC_3 = 0xD3
REG_CAL_T_NTC_4 = 0xD4
REG_CAL_T_NTC_5 = 0xD5
REG_CAL_T_NTC_6 = 0xD6
REG_CAL_T_NTC_7 = 0xD7

REG_CAP_REMAINING = 0xE0
REG_CTRL_MOSFET = 0xE1
REG_CTRL_BALANCE = 0xE2
REG_RESET = 0xE3

# Protocol commands
CMD_ENTER_FACTORY_MODE = b"\x56\x78"
CMD_EXIT_FACTORY_MODE = b"\x00\x00"
CMD_EXIT_AND_SAVE_FACTORY_MODE = b"\x28\x28"


def checksum(payload):
    return (0x10000 - sum(payload)) % 0x10000


def cmd(op, reg, data):
    payload = [reg, len(data)] + list(data)
    chksum = checksum(payload)
    data = [0xDD, op] + payload + [chksum, 0x77]
    format = f">BB{len(payload)}BHB"
    return struct.pack(format, *data)


def readCmd(reg, data=None):
    if data is None:
        data = []
    return cmd(0xA5, reg, data)


def writeCmd(reg, data=None):
    if data is None:
        data = []
    return cmd(0x5A, reg, data)


class LltJbdProtection(Protection):
    def __init__(self):
        super(LltJbdProtection, self).__init__()
        self.voltage_high_cell = False
        self.voltage_low_cell = False
        self.short = False
        self.IC_inspection = False
        self.software_lock = False

    def set_voltage_high_cell(self, value):
        self.voltage_high_cell = value
        self.cell_imbalance = (
            2 if self.voltage_low_cell or self.voltage_high_cell else 0
        )

    def set_voltage_low_cell(self, value):
        self.voltage_low_cell = value
        self.cell_imbalance = (
            2 if self.voltage_low_cell or self.voltage_high_cell else 0
        )

    def set_short(self, value):
        self.short = value
        self.set_cell_imbalance(
            2 if self.short or self.IC_inspection or self.software_lock else 0
        )

    def set_ic_inspection(self, value):
        self.IC_inspection = value
        self.set_cell_imbalance(
            2 if self.short or self.IC_inspection or self.software_lock else 0
        )

    def set_software_lock(self, value):
        self.software_lock = value
        self.set_cell_imbalance(
            2 if self.short or self.IC_inspection or self.software_lock else 0
        )


class LltJbd(Battery):
    def __init__(self, port, baud, address):
        super(LltJbd, self).__init__(port, baud, address)
        self.protection = LltJbdProtection()
        self.type = self.BATTERYTYPE
        self._product_name: str = ""
        self.has_settings = 0
        self.reset_soc = 100
        self.soc_to_set = None
        self.factory_mode = False
        self.writable = False

    # degree_sign = u'\N{DEGREE SIGN}'
    BATTERYTYPE = "LLT/JBD"
    LENGTH_CHECK = 6
    LENGTH_POS = 3

    command_general = readCmd(REG_GENERAL)  # b"\xDD\xA5\x03\x00\xFF\xFD\x77"
    command_cell = readCmd(REG_CELL)  # b"\xDD\xA5\x04\x00\xFF\xFC\x77"
    command_hardware = readCmd(REG_HARDWARE)  # b"\xDD\xA5\x05\x00\xFF\xFB\x77"

    def test_connection(self):
        # call a function that will connect to the battery, send a command and retrieve the result.
        # The result or call should be unique to this BMS. Battery name or version, etc.
        # Return True if success, False for failure
        result = False
        try:
            result = self.get_settings()
            if result:
                result = result and self.read_hardware_data()
            # get first data to show in startup log
            if result:
                result = result and self.refresh_data()
        except Exception as err:
            logger.error(f"Unexpected {err=}, {type(err)=}")
            result = False

        return result

    def product_name(self) -> str:
        return self._product_name

    def get_settings(self):
        if not self.read_gen_data():
            return False
        self.max_battery_charge_current = utils.MAX_BATTERY_CHARGE_CURRENT
        self.max_battery_discharge_current = utils.MAX_BATTERY_DISCHARGE_CURRENT
        with self.eeprom(writable=False):
            charge_over_current = self.read_serial_data_llt(readCmd(REG_CHGOC))
            if charge_over_current:
                self.max_battery_charge_current = float(
                    unpack_from(">h", charge_over_current)[0] / 100.0
                )
            discharge_over_current = self.read_serial_data_llt(readCmd(REG_DSGOC))
            if discharge_over_current:
                self.max_battery_discharge_current = float(
                    unpack_from(">h", discharge_over_current)[0] / -100.0
                )

        return True

    def reset_soc_callback(self, path, value):
        if value is None:
            return False

        if value < 0 or value > 100:
            return False

        self.reset_soc = value
        self.soc_to_set = value
        return True

    def write_soc(self):
        if self.soc_to_set is None or self.soc_to_set != 100 or not self.voltage:
            return False
        logger.info(f"write soc {self.soc_to_set}%")
        self.soc_to_set = None  # Reset value, so we will set it only once
        # TODO implement logic to map current pack readings into
        # REG_CAP_100, REG_CAP_90, REG_CAP_80, REG_CAP_70, REG_CAP_60, ...
        with self.eeprom(writable=True):
            pack_voltage = struct.pack(">H", int(self.voltage * 10))
            self.read_serial_data_llt(writeCmd(REG_CAP_100, pack_voltage))

    def refresh_data(self):
        result = self.read_gen_data()
        result = result and self.read_cell_data()
        return result

    def to_protection_bits(self, byte_data):
        tmp = bin(byte_data)[2:].rjust(13, utils.zero_char)

        self.protection.voltage_high = 2 if is_bit_set(tmp[10]) else 0
        self.protection.voltage_low = 2 if is_bit_set(tmp[9]) else 0
        self.protection.temp_high_charge = 1 if is_bit_set(tmp[8]) else 0
        self.protection.temp_low_charge = 1 if is_bit_set(tmp[7]) else 0
        self.protection.temp_high_discharge = 1 if is_bit_set(tmp[6]) else 0
        self.protection.temp_low_discharge = 1 if is_bit_set(tmp[5]) else 0
        self.protection.current_over = 1 if is_bit_set(tmp[4]) else 0
        self.protection.current_under = 1 if is_bit_set(tmp[3]) else 0

        # Software implementations for low soc
        self.protection.soc_low = (
            2
            if self.soc < utils.SOC_LOW_ALARM
            else 1
            if self.soc < utils.SOC_LOW_WARNING
            else 0
        )

        # extra protection flags for LltJbd
        self.protection.set_voltage_low_cell = is_bit_set(tmp[11])
        self.protection.set_voltage_high_cell = is_bit_set(tmp[12])
        self.protection.set_software_lock = is_bit_set(tmp[0])
        self.protection.set_IC_inspection = is_bit_set(tmp[1])
        self.protection.set_short = is_bit_set(tmp[2])

    def to_cell_bits(self, byte_data, byte_data_high):
        # init the cell array once
        if len(self.cells) == 0:
            for _ in range(self.cell_count):
                print("#" + str(_))
                self.cells.append(Cell(False))

        # get up to the first 16 cells
        tmp = bin(byte_data)[2:].rjust(min(self.cell_count, 16), utils.zero_char)
        # 4 cells
        # tmp = 0101
        # 16 cells
        # tmp = 0101010101010101

        tmp_reversed = list(reversed(tmp))
        # print(tmp_reversed) --> ['1', '0', '1', '0', '1', '0', '1', '0', '1', '0', '1', '0', '1', '0', '1', '0']
        # [cell1, cell2, cell3, ...]

        if self.cell_count > 16:
            tmp2 = bin(byte_data_high)[2:].rjust(self.cell_count - 16, utils.zero_char)
            # tmp = 1100110011001100
            tmp_reversed = tmp_reversed + list(reversed(tmp2))
            # print(tmp_reversed) --> [
            # '1', '0', '1', '0', '1', '0', '1', '0', '1', '0', '1', '0', '1', '0', '1', '0',
            # '0', '0', '1', '1', '0', '0', '1', '1', '0', '0', '1', '1', '0', '0', '1', '1'
            # ]
            # [
            # cell1, cell2, ..., cell16,
            # cell17, cell18, ..., cell32
            # ]

        for c in range(self.cell_count):
            if is_bit_set(tmp_reversed[c]):
                self.cells[c].balance = True
            else:
                self.cells[c].balance = False

        """
        # clear the list
        for c in self.cells:
            self.cells.remove(c)
        # get up to the first 16 cells
        tmp = bin(byte_data)[2:].rjust(min(self.cell_count, 16), utils.zero_char)
        for bit in reversed(tmp):
            self.cells.append(Cell(is_bit_set(bit)))
        # get any cells above 16
        if self.cell_count > 16:
            tmp = bin(byte_data_high)[2:].rjust(self.cell_count - 16, utils.zero_char)
            for bit in reversed(tmp):
                self.cells.append(Cell(is_bit_set(bit)))
        """

    def to_fet_bits(self, byte_data):
        tmp = bin(byte_data)[2:].rjust(2, utils.zero_char)
        self.charge_fet = is_bit_set(tmp[1])
        self.discharge_fet = is_bit_set(tmp[0])

    def read_gen_data(self):
        gen_data = self.read_serial_data_llt(self.command_general)
        # check if connect success
        if gen_data is False or len(gen_data) < 27:
            return False

        (
            voltage,
            current,
            capacity_remain,
            capacity,
            self.cycles,
            self.production,
            balance,
            balance2,
            protection,
            version,
            soc,
            fet,
            self.cell_count,
            self.temp_sensors,
        ) = unpack_from(">HhHHHHhHHBBBBB", gen_data)
        self.voltage = voltage / 100
        self.current = current / 100
        self.soc = round(100 * capacity_remain / capacity, 2)
        self.capacity_remain = capacity_remain / 100
        self.capacity = capacity / 100
        self.to_cell_bits(balance, balance2)
        self.hardware_version = float(
            str(version >> 4 & 0x0F) + "." + str(version & 0x0F)
        )
        self.to_fet_bits(fet)
        self.to_protection_bits(protection)
        self.max_battery_voltage = utils.MAX_CELL_VOLTAGE * self.cell_count
        self.min_battery_voltage = utils.MIN_CELL_VOLTAGE * self.cell_count

        # 0 = MOS, 1 = temp 1, 2 = temp 2
        for t in range(self.temp_sensors):
            temp1 = unpack_from(">H", gen_data, 23 + (2 * t))[0]
            self.to_temp(t, utils.kelvin_to_celsius(temp1 / 10))

        return True

    def read_cell_data(self):
        cell_data = self.read_serial_data_llt(self.command_cell)
        # check if connect success
        if cell_data is False or len(cell_data) < self.cell_count * 2:
            return False

        for c in range(self.cell_count):
            try:
                cell_volts = unpack_from(">H", cell_data, c * 2)
                if len(cell_volts) != 0:
                    self.cells[c].voltage = cell_volts[0] / 1000
            except struct.error:
                self.cells[c].voltage = 0
        return True

    def read_hardware_data(self):
        hardware_data = self.read_serial_data_llt(self.command_hardware)
        # check if connection success
        if hardware_data is False:
            return False

        self._product_name = unpack_from(
            ">" + str(len(hardware_data)) + "s", hardware_data
        )[0].decode()
        logger.debug(self._product_name)
        return True

    @staticmethod
    def validate_packet(data):
        if not data:
            return False

        if data is False:
            return False

        start, op, status, payload_length = unpack_from("BBBB", data)
        if start != 0xDD:
            logger.error(
                ">>> ERROR: Invalid response packet. Expected begin packet character 0xDD"
            )
        if status != 0x0:
            logger.warn(">>> WARN: BMS rejected request. Status " + status)
            return False
        if len(data) != payload_length + 7:
            logger.error(
                ">>> ERROR: BMS send insufficient data. Received "
                + str(len(data))
                + " expected "
                + str(payload_length + 7)
            )
            return False
        chk_sum, end = unpack_from(">HB", data, payload_length + 4)
        if end != 0x77:
            logger.error(
                ">>> ERROR: Incorrect Reply. Expected end packet character 0x77"
            )
            return False
        if chk_sum != checksum(data[2:-3]):
            logger.error(">>> ERROR: Invalid checksum.")
            return False

        payload = data[4 : payload_length + 4]

        return payload

    def read_serial_data_llt(self, command):
        data = read_serial_data(
            command, self.port, self.baud_rate, self.LENGTH_POS, self.LENGTH_CHECK
        )
        return self.validate_packet(data)

    def __enter__(self):
        if self.read_serial_data_llt(
            writeCmd(REG_ENTER_FACTORY, CMD_ENTER_FACTORY_MODE)
        ):
            self.factory_mode = True

    def __exit__(self, type, value, traceback):
        cmd_value = (
            CMD_EXIT_AND_SAVE_FACTORY_MODE if self.writable else CMD_EXIT_FACTORY_MODE
        )
        if self.factory_mode:
            if not self.read_serial_data_llt(writeCmd(REG_EXIT_FACTORY, cmd_value)):
                logger.error(">>> ERROR: Unable to exit factory mode.")
            else:
                self.factory_mode = False
                self.writable = False

    def eeprom(self, writable=False):
        self.writable = writable
        return self
