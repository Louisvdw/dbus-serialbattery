# -*- coding: utf-8 -*-
from battery import Protection, Battery, Cell
from utils import logger
import utils
import serial


class Seplos(Battery):
    def __init__(self, port, baud, address=0x00):
        super(Seplos, self).__init__(port, baud, address)
        self.type = self.BATTERYTYPE
        self.poll_interval = 5000

    BATTERYTYPE = "Seplos"

    COMMAND_STATUS = 0x42
    COMMAND_ALARM = 0x44
    COMMAND_PROTOCOL_VERSION = 0x4F
    COMMAND_VENDOR_INFO = 0x51

    @staticmethod
    def int_from_1byte_hex_ascii(data: bytes, offset: int, signed=False):
        return int.from_bytes(
            bytes.fromhex(data[offset : offset + 2].decode("ascii")),
            byteorder="big",
            signed=signed,
        )

    @staticmethod
    def int_from_2byte_hex_ascii(data: bytes, offset: int, signed=False):
        return int.from_bytes(
            bytes.fromhex(data[offset : offset + 4].decode("ascii")),
            byteorder="big",
            signed=signed,
        )

    @staticmethod
    def get_checksum(frame: bytes) -> int:
        """implements the Seplos checksum algorithm, returns 4 bytes"""
        checksum = 0
        for b in frame:
            checksum += b
        checksum %= 0xFFFF
        checksum ^= 0xFFFF
        checksum += 1
        return checksum

    @staticmethod
    def get_info_length(info: bytes) -> int:
        """implements the Seplos checksum for the info length"""
        lenid = len(info)
        if lenid == 0:
            return 0

        lchksum = (lenid & 0xF) + ((lenid >> 4) & 0xF) + ((lenid >> 8) & 0xF)
        lchksum %= 16
        lchksum ^= 0xF
        lchksum += 1

        return (lchksum << 12) + lenid

    @staticmethod
    def encode_cmd(address: int, cid2: int, info: bytes = b"") -> bytes:
        """encodes a command sent to a battery (cid1=0x46)"""
        cid1 = 0x46

        info_length = Seplos.get_info_length(info)

        frame = "{:02X}{:02X}{:02X}{:02X}{:04X}".format(
            0x20, address, cid1, cid2, info_length
        ).encode()
        frame += info

        checksum = Seplos.get_checksum(frame)
        encoded = b"~" + frame + "{:04X}".format(checksum).encode() + b"\r"
        return encoded

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

        # give the user a feedback that no BMS was found
        if not result:
            logger.error(">>> ERROR: No reply - returning")

        return result

    def get_settings(self):
        # After successful connection get_settings will be called to set up the battery.
        # Set the current limits, populate cell count, etc.
        # Return True if success, False for failure

        # BMS does not provide max charge-/discharge, so we have to use hardcoded/config values
        self.max_battery_charge_current = utils.MAX_BATTERY_CHARGE_CURRENT
        self.max_battery_discharge_current = utils.MAX_BATTERY_DISCHARGE_CURRENT

        self.max_battery_voltage = utils.MAX_CELL_VOLTAGE * self.cell_count
        self.min_battery_voltage = utils.MIN_CELL_VOLTAGE * self.cell_count

        # init the cell array
        for _ in range(self.cell_count):
            self.cells.append(Cell(False))

        return True

    def refresh_data(self):
        # call all functions that will refresh the battery data.
        # This will be called for every iteration (self.poll_interval)
        # Return True if success, False for failure
        result_status = self.read_status_data()
        result_alarm = self.read_alarm_data()

        return result_status and result_alarm

    @staticmethod
    def decode_alarm_byte(data_byte: int, alarm_bit: int, warn_bit: int):
        if data_byte & (1 << alarm_bit) != 0:
            return Protection.ALARM
        if data_byte & (1 << warn_bit) != 0:
            return Protection.WARNING
        return Protection.OK

    def read_alarm_data(self):
        logger.debug("read alarm data")
        data = self.read_serial_data_seplos(
            self.encode_cmd(address=0x00, cid2=self.COMMAND_ALARM, info=b"01")
        )
        # check if we could successfully read data and we have the expected length of 98 bytes
        if data is False or len(data) != 98:
            return False

        try:
            logger.debug("alarm info raw {}".format(data))
            return self.decode_alarm_data(bytes.fromhex(data.decode("ascii")))
        except (ValueError, UnicodeDecodeError) as e:
            logger.warning("could not hex-decode raw alarm data", exc_info = e)
            return False

    def decode_alarm_data(self, data: bytes):
        logger.debug("alarm info decoded {}".format(data))
        voltage_alarm_byte = data[30]
        self.protection.voltage_cell_low = Seplos.decode_alarm_byte(
            data_byte=voltage_alarm_byte, alarm_bit=3, warn_bit=2
        )
        # cell high voltage is actually unused because DBUS does not seem to support it, decoding anyway
        # c.f. https://github.com/victronenergy/venus/wiki/dbus#battery
        self.protection.voltage_cell_high = Seplos.decode_alarm_byte(
            data_byte=voltage_alarm_byte, alarm_bit=1, warn_bit=0
        )
        self.protection.voltage_low = Seplos.decode_alarm_byte(
            data_byte=voltage_alarm_byte, alarm_bit=7, warn_bit=6
        )
        self.protection.voltage_high = Seplos.decode_alarm_byte(
            data_byte=voltage_alarm_byte, alarm_bit=5, warn_bit=4
        )

        temperature_alarm_byte = data[31]
        self.protection.temp_low_charge = Seplos.decode_alarm_byte(
            data_byte=temperature_alarm_byte, alarm_bit=3, warn_bit=2
        )
        self.protection.temp_high_charge = Seplos.decode_alarm_byte(
            data_byte=temperature_alarm_byte, alarm_bit=1, warn_bit=0
        )
        self.protection.temp_low_discharge = Seplos.decode_alarm_byte(
            data_byte=temperature_alarm_byte, alarm_bit=7, warn_bit=6
        )
        self.protection.temp_high_discharge = Seplos.decode_alarm_byte(
            data_byte=temperature_alarm_byte, alarm_bit=5, warn_bit=4
        )

        current_alarm_byte = data[33]
        self.protection.current_over = Seplos.decode_alarm_byte(
            data_byte=current_alarm_byte, alarm_bit=1, warn_bit=0
        )
        self.protection.current_under = Seplos.decode_alarm_byte(
            data_byte=current_alarm_byte, alarm_bit=3, warn_bit=2
        )

        soc_alarm_byte = data[34]
        self.protection.soc_low = Seplos.decode_alarm_byte(
            data_byte=soc_alarm_byte, alarm_bit=3, warn_bit=2
        )

        switch_byte = data[35]
        self.discharge_fet = True if switch_byte & 0b01 != 0 else False
        self.charge_fet = True if switch_byte & 0b10 != 0 else False
        return True

    def read_status_data(self):
        logger.debug("read status data")

        data = self.read_serial_data_seplos(
            self.encode_cmd(address=0x00, cid2=0x42, info=b"01")
        )

        # check if reading data was successful and has the expected data length of 150 byte
        if data is False or len(data) != 150:
            return False

        self.decode_status_data(data)

        return True

    def decode_status_data(self, data):
        cell_count_offset = 4
        voltage_offset = 6
        temps_offset = 72
        self.cell_count = Seplos.int_from_1byte_hex_ascii(
            data=data, offset=cell_count_offset
        )
        if self.cell_count == len(self.cells):
            for i in range(self.cell_count):
                voltage = (
                    Seplos.int_from_2byte_hex_ascii(data, voltage_offset + i * 4) / 1000
                )
                self.cells[i].voltage = voltage
                logger.debug("Voltage cell[{}]={}V".format(i, voltage))
            for i in range(min(4, self.cell_count)):
                temp = (
                    Seplos.int_from_2byte_hex_ascii(data, temps_offset + i * 4) - 2731
                ) / 10
                self.cells[i].temp = temp
                logger.debug("Temp cell[{}]={}°C".format(i, temp))
        self.temp1 = (
            Seplos.int_from_2byte_hex_ascii(data, temps_offset + 4 * 4) - 2731
        ) / 10
        self.temp2 = (
            Seplos.int_from_2byte_hex_ascii(data, temps_offset + 5 * 4) - 2731
        ) / 10
        self.current = (
            Seplos.int_from_2byte_hex_ascii(data, offset=96, signed=True) / 100
        )
        self.voltage = Seplos.int_from_2byte_hex_ascii(data, offset=100) / 100
        self.capacity_remain = Seplos.int_from_2byte_hex_ascii(data, offset=104) / 100
        self.capacity = Seplos.int_from_2byte_hex_ascii(data, offset=110) / 100
        self.soc = Seplos.int_from_2byte_hex_ascii(data, offset=114) / 10
        self.cycles = Seplos.int_from_2byte_hex_ascii(data, offset=122)
        self.hardware_version = "Seplos BMS {} cells".format(self.cell_count)
        logger.debug("Current = {}A , Voltage = {}V".format(self.current, self.voltage))
        logger.debug(
            "Capacity = {}/{}Ah , SOC = {}%".format(
                self.capacity_remain, self.capacity, self.soc
            )
        )
        logger.debug("Cycles = {}".format(self.cycles))
        logger.debug(
            "Environment temp = {}°C ,  Power temp = {}°C".format(
                self.temp1, self.temp2
            )
        )
        logger.debug("HW:" + self.hardware_version)


    @staticmethod
    def is_valid_frame(data: bytes) -> bool:
        """checks if data contains a valid frame
        * minimum length is 18 Byte
        * checksum needs to be valid
        * also checks for error code as return code in cid2
        * not checked: lchksum
        """
        if len(data) < 18:
            logger.warning("short read, data={}".format(data))
            return False

        chksum = Seplos.get_checksum(data[1:-5])
        if chksum != Seplos.int_from_2byte_hex_ascii(data, -5):
            logger.warning("checksum error")
            return False

        cid2 = data[7:9]
        if cid2 != b"00":
            logger.warning("command returned with error code {}".format(cid2))
            return False

        return True

    def read_serial_data_seplos(self, command):
        logger.debug("read serial data seplos")

        with serial.Serial(self.port, baudrate=self.baud_rate, timeout=1) as ser:
            ser.flushOutput()
            ser.flushInput()
            written = ser.write(command)
            logger.debug(
                "wrote {} bytes to serial port {}, command={}".format(
                    written, self.port, command
                )
            )

            data = ser.readline()

            if not Seplos.is_valid_frame(data):
                return False

            length_pos = 10
            return_data = data[length_pos + 3 : -5]
            info_length = Seplos.int_from_2byte_hex_ascii(b"0" + data[length_pos:], 0)
            logger.debug(
                "returning info data of length {}, info_length is {} : {}".format(len(return_data), info_length, return_data)
            )

            return return_data
