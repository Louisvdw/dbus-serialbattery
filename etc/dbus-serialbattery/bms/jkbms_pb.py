# -*- coding: utf-8 -*-
from battery import Battery, Cell
from utils import is_bit_set, read_serial_data, logger
import utils
from struct import unpack_from
from re import sub
import sys


class Jkbms(Battery):
    def __init__(self, port, baud, address):
        super(Jkbms, self).__init__(port, baud, address)
        self.type = self.BATTERYTYPE
        self.unique_identifier_tmp = ""
        self.cell_count = 16

    BATTERYTYPE = "Jkbms"
    LENGTH_CHECK = 0
    LENGTH_POS = 2
    LENGTH_SIZE = "H"
    CURRENT_ZERO_CONSTANT = 32768
    command_status = b"\x01\x10\x16\x20\x00\x01\x02\x00\x00\xD6\xF1"

    def test_connection(self):
        # call a function that will connect to the battery, send a command and retrieve the result.
        # The result or call should be unique to this BMS. Battery name or version, etc.
        # Return True if success, False for failure
        try:
            return self.read_status_data()
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
            return False

    def get_settings(self):
        # After successful  connection get_settings will be call to set up the battery.
        # Set the current limits, populate cell count, etc
        # Return True if success, False for failure
        self.max_battery_voltage = utils.MAX_CELL_VOLTAGE * self.cell_count
        self.min_battery_voltage = utils.MIN_CELL_VOLTAGE * self.cell_count

        # init the cell array
        for _ in range(self.cell_count):
            self.cells.append(Cell(False))

        self.hardware_version = (
            "JKBMS "
            + str(self.cell_count)
            + " cells"
            + (" (" + self.production + ")" if self.production else "")
        )
        return True

    def refresh_data(self):
        # call all functions that will refresh the battery data.
        # This will be called for every iteration (1 second)
        # Return True if success, False for failure
        result = self.read_status_data()

        return result

    def get_data(self, bytes, idcode, start, length):
        # logger.debug("start "+str(start) + " length " + str(length))
        # logger.debug(binascii.hexlify(bytearray(bytes[start:start + 1 + length])).decode('ascii'))
        start = bytes.find(idcode, start, start + 1 + length)
        if start < 0:
            return False
        return bytes[start + 1 : start + length + 1]

    def read_status_data(self):
        status_data = self.read_serial_data_jkbms(self.command_status)
        # check if connection success
        if status_data is False:
            return False

#        logger.error("sucess we have data")
#        be = ''.join(format(x, ' 02X') for x in status_data)
#        logger.error(be)

#55 adress
#AA function
#EB 90 02 05 no idea what this is 235, 144, 2, 5
#[6] 04 0D .. cell voltage 1
#[8] 04 0D .. cell voltage 2
#FF FF 00 00  Cell sta?
#06 0D avg voltage
#02 00 max diff
#02 max nr
#00 min nr
#[144] D1 00 temp mos .. 00 D1 = 209 -> 20.9
#[146] 00 00 00 00 
#[150] 58 D0 00 00 ... battery voltage
#[154] 00 00 00 00 ... battery mWatt 
#[158] 00 00 00 00 ... battery mA
#[162] C8 00 ... Temp sensor 1
#[164] CB 00 ... Temp sensor 2
#[166] 00 00 00 00 .. bits
#[170] 00 00 .. balance current
#[172] 00 .. balancer state ..0..1..2
#[173] 64 .. soc state
#[174] 84 45 04 00 soc cap remain
#[178] C0 45 04 00 SOCFullChargeCap
#[182] 00 00 00 00 cycle count
#[186] 1B 00 00 00 cycle remaining capacity
#[190] 64 SOH
#[191] 00 Precharge
#[192] 00 00 User alarm
#[194] 0B B5 03 00 runtime
#[198] 00 00 charge / discharge
#[200] 00 00 00 00 00 00 00 00 00 00 00 00 00 00 FF 00 01 00 00 00 9D 03 00 00 00 00 EC 70 3F 40 00 00 00 00 D5 14 00 00 00 01 01 01 04 06 00 00 95 0C 02 00 00 00 00 00 D1 00 C5 00 CD 00 E8 03 B0 56 5B 08 11 00 00 00 80 51 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 FE FF 7F DC 2F 01 01 B0 07 00 00 00 62 01 10 16 20 00 01 04 4B

        # cell voltages
        for c in range(32):
                if((unpack_from("<H", status_data, c * 2 + 6)[0] / 1000)!=0):
                        if(len(self.cells)<=c):
                                self.cells.append(Cell(False))
                        self.cells[c].voltage = (
                                unpack_from("<H", status_data, c * 2 + 6)[0] / 1000)
                        self.cell_count = len(self.cells)
                        logger.error("Cell "+str(c)+" voltage:"+str(self.cells[c].voltage)+"V")

        # MOSFET temperature
        temp_mos = unpack_from("<h", status_data, 144)[0] / 10
        self.to_temp(0, temp_mos if temp_mos < 99 else (100 - temp_mos))
        logger.error("Mos Temperature: "+str(temp_mos))

        # Temperature sensors
        temp1 = unpack_from("<h", status_data, 162)[0] / 10
        temp2 = unpack_from("<h", status_data, 164)[0] / 10
        self.to_temp(1, temp1 if temp1 < 99 else (100 - temp1))
        self.to_temp(2, temp2 if temp2 < 99 else (100 - temp2))
        logger.error("Temp 2:"+str(temp1))
        logger.error("Temp 3:"+str(temp2))

        # Battery voltage
        self.voltage = unpack_from("<I", status_data, 150)[0] / 1000
        logger.error("voltage: "+str(self.voltage)+"V")

        # Battery ampere
        self.current = unpack_from("<i", status_data, 154)[0] / 1000
        logger.error("Current:"+str(self.current))

        # Continued discharge current
#        offset = cellbyte_count + 66
#        self.max_battery_discharge_current = float(
#            unpack_from(">H", self.get_data(status_data, b"\x97", offset, 2))[0]
#        )

        # Continued charge current
#        offset = cellbyte_count + 72
#        self.max_battery_charge_current = float(
#            unpack_from(">H", self.get_data(status_data, b"\x99", offset, 2))[0]
#        )

        # SOC
        self.soc = unpack_from("<B", status_data, 173)[0]
        logger.error("SOC: "+str(self.soc)+"%")

        # cycles
        self.cycles = unpack_from("<I", status_data, 182)[0]

#        self.capacity_remain = unpack_from('>L', self.get_data(status_data, b'\x89', offset, 4))[0]
#        self.capacity = unpack_from(
#            ">L", self.get_data(status_data, b"\xAA", offset, 4)
#        )[0]

#        self.to_protection_bits(
#            unpack_from(">H", self.get_data(status_data, b"\x8B", offset, 2))[0]
#        )

        # bits
        bal = unpack_from("<B", status_data, 172)[0]
        charge = unpack_from("<B", status_data, 198)[0]
        discharge = unpack_from("<B", status_data, 199)[0]
        self.charge_fet = 1 if charge != 0 else 0
        self.discharge_fet = 1 if discharge !=0 else 0
        self.balancing = 1 if bal !=0 else 0

#        self.version = unpack_from(
#            ">15s", self.get_data(status_data, b"\xB7", offset, 15)
#        )[0].decode()

#        self.unique_identifier_tmp = sub(
#            " +",
#            "_",
#            (
#                unpack_from(">24s", self.get_data(status_data, b"\xBA", offset, 24))[0]
#                .decode()
#                .replace("\x00", " ")
#                .replace("Input Userda", "")
#                .strip()
#            ),
#        )

        # show wich cells are balancing
        if self.get_min_cell() is not None and self.get_max_cell() is not None:
            for c in range(self.cell_count):
                if self.balancing and (
                    self.get_min_cell() == c or self.get_max_cell() == c
                ):
                    self.cells[c].balance = True
                else:
                    self.cells[c].balance = False

        # logger.info(self.hardware_version)
        return True

    def unique_identifier(self) -> str:
        """
        Used to identify a BMS when multiple BMS are connected
        """
        return self.unique_identifier_tmp

    def to_balance_bits(self, byte_data):
        tmp = bin(byte_data)[2:]
        self.balance_fet = is_bit_set(tmp)

    def get_balancing(self):
        return 1 if self.balancing else 0

    def get_min_cell(self):
        min_voltage = 9999
        min_cell = None
        for c in range(min(len(self.cells), self.cell_count)):
            if (
                self.cells[c].voltage is not None
                and min_voltage > self.cells[c].voltage
            ):
                min_voltage = self.cells[c].voltage
                min_cell = c
        return min_cell

    def get_max_cell(self):
        max_voltage = 0
        max_cell = None
        for c in range(min(len(self.cells), self.cell_count)):
            if (
                self.cells[c].voltage is not None
                and max_voltage < self.cells[c].voltage
            ):
                max_voltage = self.cells[c].voltage
                max_cell = c
        return max_cell

    def to_protection_bits(self, byte_data):
        """
        Bit 0: Low capacity alarm: 1 warning only, 0 nomal -> OK
        Bit 1: MOS tube overtemperature alarm: 1 alarm, 0 nomal -> OK
        Bit 2: Charge over voltage alarm: 1 alarm, 0 nomal -> OK
        Bit 3: Discharge undervoltage alarm: 1 alarm, 0 nomal -> OK
        Bit 4: Battery overtemperature alarm: 1 alarm, 0 nomal -> OK
        Bit 5: Charge overcurrent alarm: 1 alarm, 0 nomal -> OK
        Bit 6: discharge over current alarm: 1 alarm, 0 nomal -> OK
        Bit 7: core differential pressure alarm: 1 alarm, 0 nomal -> OK
        Bit 8: overtemperature alarm in the battery box: 1 alarm, 0 nomal -> OK
        Bit 9: Battery low temperature alarm: 1 alarm, 0 nomal -> OK
        Bit 10: Unit overvoltage: 1 alarm, 0 nomal -> OK
        Bit 11: Unit undervoltage: 1 alarm, 0 nomal -> OK
        Bit 12:309_A protection: 1 alarm, 0 nomal
        Bit 13:309_B protection: 1 alarm, 0 nomal
        """
        pos = 13
        tmp = bin(byte_data)[15 - pos :].rjust(pos + 1, utils.zero_char)
        # logger.debug(tmp)

        # low capacity alarm
        self.protection.soc_low = 2 if is_bit_set(tmp[pos - 0]) else 0
        # MOSFET temperature alarm
        self.protection.temp_high_internal = 2 if is_bit_set(tmp[pos - 1]) else 0
        # charge over voltage alarm
        # TODO: check if "self.soc_reset_requested is False" works,
        # else use "self.soc_reset_last_reached < int(time()) - (60 * 60)"
        self.protection.voltage_high = 2 if is_bit_set(tmp[pos - 2]) else 0
        # discharge under voltage alarm
        self.protection.voltage_low = 2 if is_bit_set(tmp[pos - 3]) else 0
        # charge overcurrent alarm
        self.protection.current_over = 1 if is_bit_set(tmp[pos - 5]) else 0
        # discharge over current alarm
        self.protection.current_under = 1 if is_bit_set(tmp[pos - 6]) else 0
        # core differential pressure alarm OR unit overvoltage alarm
        self.protection.cell_imbalance = (
            2 if is_bit_set(tmp[pos - 7]) else 1 if is_bit_set(tmp[pos - 10]) else 0
        )
        # unit undervoltage alarm
        self.protection.voltage_cell_low = 1 if is_bit_set(tmp[pos - 11]) else 0
        # battery overtemperature alarm OR overtemperature alarm in the battery box
        alarm_temp_high = (
            1 if is_bit_set(tmp[pos - 4]) or is_bit_set(tmp[pos - 8]) else 0
        )
        # battery low temperature alarm
        alarm_temp_low = 1 if is_bit_set(tmp[pos - 9]) else 0
        # check if low/high temp alarm arise during charging
        self.protection.temp_high_charge = (
            1 if self.current > 0 and alarm_temp_high == 1 else 0
        )
        self.protection.temp_low_charge = (
            1 if self.current > 0 and alarm_temp_low == 1 else 0
        )
        # check if low/high temp alarm arise during discharging
        self.protection.temp_high_discharge = (
            1 if self.current <= 0 and alarm_temp_high == 1 else 0
        )
        self.protection.temp_low_discharge = (
            1 if self.current <= 0 and alarm_temp_low == 1 else 0
        )

    def read_serial_data_jkbms(self, command: str) -> bool:
        """
        use the read_serial_data() function to read the data and then do BMS specific checks (crc, start bytes, etc)
        :param command: the command to be sent to the bms
        :return: True if everything is fine, else False
        """
        data = read_serial_data(
            command,
            self.port,
            115200,
            self.LENGTH_POS,
            0,
            307,
            self.LENGTH_SIZE,
        )
        if data is False:
            return False

        start, length = unpack_from(">HH", data)
        end, crc_hi, crc_lo = unpack_from(">BHH", data[-5:])

        s = sum(data[0:-4])

        logger.debug("bytearray: " + utils.bytearray_to_string(data))

        if start == 0x4E57 and end == 0x68 and s == crc_lo:
            return data[10 : length - 7]
        elif s != crc_lo:
            logger.error(
                "CRC checksum mismatch: Expected 0x%04x, Got 0x%04x" % (crc_lo, s)
            )
            return data
            return False
        else:
            logger.error(">>> ERROR: Incorrect Reply ")
            return data
            return False
