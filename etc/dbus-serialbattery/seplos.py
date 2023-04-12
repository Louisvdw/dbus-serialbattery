# -*- coding: utf-8 -*-
from battery import Protection, Battery, Cell
from utils import *


def int_from_hex_ascii(to_decode, signed=False):
    return int.from_bytes(bytes.fromhex(to_decode.decode('ascii')), byteorder="big", signed=signed)


class Seplos(Battery):
    def __init__(self, port, baud, address):
        super(Seplos, self).__init__(port, baud, address)
        self.type = self.BATTERYTYPE
        self.poll_interval = 5000

    BATTERYTYPE = "Seplos"

    COMMAND_STATUS = 0x42
    COMMAND_ALARM = 0x44
    COMMAND_PROTOCOL_VERSION = 0x4f
    COMMAND_VENDOR_INFO = 0x51

    @staticmethod
    def int_from_1byte_hex_ascii(data: bytes, offset: int, signed=False):
        return int.from_bytes(bytes.fromhex(data[offset:offset+2].decode('ascii')), byteorder="big", signed=signed)

    @staticmethod
    def int_from_2byte_hex_ascii(data: bytes, offset: int, signed=False):
        return int.from_bytes(bytes.fromhex(data[offset:offset+4].decode('ascii')), byteorder="big", signed=signed)

    @staticmethod
    def get_checksum(frame: bytes) -> int:
        """ implements the Seplos checksum algorithm, returns 4 bytes
        """
        checksum = 0
        for b in frame:
            checksum += b
        checksum %= 0xffff
        checksum ^= 0xffff
        checksum += 1
        return checksum

    @staticmethod
    def get_info_length(info: bytes) -> int:
        """ implements the Seplos checksum for the info length
        """
        lenid = len(info)
        if lenid == 0:
            return 0

        lchksum = (lenid & 0xf) + ((lenid >> 4) & 0xf) + ((lenid >> 8) & 0xf)
        lchksum %= 16
        lchksum ^= 0xf
        lchksum += 1

        return (lchksum << 12) + lenid


    @staticmethod
    def encode_cmd(address: int, cid2: int, info: bytes = b'') -> bytes:
        """ encodes a command sent to a battery (cid1=0x46)
        """
        cid1 = 0x46

        info_length = Seplos.get_info_length(info)

        frame = '{:02X}{:02X}{:02X}{:02X}{:04X}'.format(0x20, address, cid1, cid2, info_length).encode()
        frame += info

        checksum = Seplos.get_checksum(frame)
        encoded = (b"~" + frame + "{:04X}".format(checksum).encode() + b"\r")
        return encoded

    def test_connection(self):
        # call a function that will connect to the battery, send a command and retrieve the result.
        # The result or call should be unique to this BMS. Battery name or version, etc.
        # Return True if success, False for failure

        try:
            return self.read_status_data()
        except Exception as err:
            logger.error(f"Unexpected {err=}, {type(err)=}")
            return False

    def get_settings(self):
        # After successful  connection get_settings will be call to set up the battery.
        # Set the current limits, populate cell count, etc.
        # Return True if success, False for failure

        # Uncomment if BMS does not supply capacity
        # self.capacity = BATTERY_CAPACITY
        self.max_battery_charge_current = MAX_BATTERY_CHARGE_CURRENT
        self.max_battery_discharge_current = MAX_BATTERY_DISCHARGE_CURRENT
        self.max_battery_voltage = MAX_CELL_VOLTAGE * self.cell_count
        self.min_battery_voltage = MIN_CELL_VOLTAGE * self.cell_count

        # init the cell array
        for _ in range(self.cell_count):
            self.cells.append(Cell(False))

        return True

    def refresh_data(self):
        # call all functions that will refresh the battery data.
        # This will be called for every iteration (1 second)
        # Return True if success, False for failure
        result = self.read_status_data()

        return result


    def read_alarm_data(self):
        logger.info("read alarm data")
        data = self.read_serial_data_seplos(self.encode_cmd(address=0x00, cid2=self.COMMAND_ALARM, info=b"01"))
        # check if connection success
        if data is False:
            return False

        logger.info("alarm info {}".format(bytes.fromhex(data.decode('ascii'))))
        return True

    def read_status_data(self):
        logger.debug("read status data")
        data = self.read_serial_data_seplos(self.encode_cmd(address=0x00, cid2=0x42, info=b"01"))

        # check if connection success
        if data is False:
            return False

        cell_count_offset = 4
        voltage_offset = 6
        temps_offset = 72
        self.cell_count = Seplos.int_from_1byte_hex_ascii(data=data, offset=cell_count_offset)
        if self.cell_count == len(self.cells):
            for i in range(self.cell_count):
                v = Seplos.int_from_2byte_hex_ascii(data, voltage_offset + i*4) / 1000
                self.cells[i].voltage = v
                logger.debug("Voltage cell[{}]={}V".format(i,v))
            for i in range(min(4, self.cell_count)):
                t = (Seplos.int_from_2byte_hex_ascii(data, temps_offset + i*4) - 2731) / 10
                self.cells[i].temp = t
                logger.debug("Temp cell[{}]={}°C".format(i,t))

        self.temp1 = (Seplos.int_from_2byte_hex_ascii(data, temps_offset + 4*4) - 2731) / 10
        self.temp2 = (Seplos.int_from_2byte_hex_ascii(data, temps_offset + 5*4) - 2731) / 10
        self.current = Seplos.int_from_2byte_hex_ascii(data, offset = 96, signed=True)/100
        self.voltage = Seplos.int_from_2byte_hex_ascii(data, offset = 100)/100
        self.capacity_remain = Seplos.int_from_2byte_hex_ascii(data, offset=104)/100
        self.capacity        = Seplos.int_from_2byte_hex_ascii(data, offset=110)/100
        self.soc             = Seplos.int_from_2byte_hex_ascii(data, offset=114)/10
        self.cycles          = Seplos.int_from_2byte_hex_ascii(data, offset=122)
        self.hardware_version = "Seplos BMS {} cells".format(self.cell_count)

        logger.debug("Current = {}A , Voltage = {}V".format(self.current, self.voltage))
        logger.debug("Capacity = {}/{}Ah , SOC = {}%".format(self.capacity_remain, self.capacity, self.soc))
        logger.debug("Cycles = {}".format(self.cycles))
        logger.debug("Environment temp = {}°C ,  Power temp = {}°C".format(self.temp1, self.temp2))
        logger.debug("HW:" + self.hardware_version)

        # TODO: read alarms?
        return True


    @staticmethod
    def is_frame_valid(data: bytes) -> bool:
        """ checks if data contains a valid frame
        * minimum length is 18 Byte
        * checksum needs to be valid
        * also checks for error code as return code in cid2
        * not checked: lchksum
        """
        if len(data) < 18:
            logger.warning('short read, data={}'.format(data))
            return False

        chksum = Seplos.get_checksum(data[1: -5])
        if chksum != Seplos.int_from_2byte_hex_ascii(data, -5):
            logger.warning("checksum error")
            return False

        cid2 = data[7:9]
        if cid2 != b'00':
            logger.warning('command returned with error code {}'.format(cid2))
            return False

        return True

    def read_serial_data_seplos(self, command):
        logger.debug("read serial data seplos")

        with serial.Serial(self.port, baudrate=self.baud_rate, timeout=1) as ser:
            ser.flushOutput()
            ser.flushInput()
            written = ser.write(command)
            logger.debug("wrote {} bytes to serial port {}, command={}".format(written, self.port, command))

            data = ser.readline()

            if not Seplos.is_frame_valid(data):
                return False

            length_pos = 10
            return_data = data[length_pos + 3 : -5]
            info_length = Seplos.int_from_2byte_hex_ascii( b"0" + data[length_pos:], 0)
            logger.debug("return info data of length {} : {}".format(info_length, return_data))

            return return_data