# -*- coding: utf-8 -*-
from battery import Battery, Cell
from utils import read_serial_data, unpack_from, logger
import utils
from struct import unpack
import struct


class Renogy(Battery):
    def __init__(self, port, baud, address):
        super(Renogy, self).__init__(port, baud, address)
        self.type = self.BATTERYTYPE

        # The RBT100LFP12SH-G1 uses 0xF7, another battery uses 0x30
        self.command_address = address

    BATTERYTYPE = "Renogy"
    LENGTH_CHECK = 4
    LENGTH_POS = 2

    # command bytes [Address field][Function code (03 = Read register)]
    #                   [Register Address (2 bytes)][Data Length (2 bytes)][CRC (2 bytes little endian)]
    command_read = b"\x03"
    # Core data = voltage, temp, current, soc
    command_cell_count = b"\x13\x88\x00\x01"  # Register  5000
    command_cell_voltages = b"\x13\x89\x00\x04"  # Registers 5001-5004
    command_cell_temps = b"\x13\x9A\x00\x04"  # Registers 5018-5021
    command_total_voltage = b"\x13\xB3\x00\x01"  # Register  5043
    command_bms_temp1 = b"\x13\xAD\x00\x01"  # Register  5037
    command_bms_temp2 = b"\x13\xB0\x00\x01"  # Register  5040
    command_current = b"\x13\xB2\x00\x01"  # Register  5042 (signed int)
    command_capacity = b"\x13\xB6\x00\x02"  # Registers 5046-5047 (long)
    command_soc = b"\x13\xB2\x00\x04"  # Registers 5042-5045 (amps, volts, soc as long)
    # Battery info
    command_manufacturer = b"\x14\x0C\x00\x08"  # Registers 5132-5139 (8 byte string)
    command_model = b"\x14\x02\x00\x08"  # Registers 5122-5129 (8 byte string)
    command_serial_number = b"\x13\xF6\x00\x08"  # Registers 5110-5117 (8 byte string)
    command_firmware_version = (
        b"\x14\x0A\x00\x02"  # Registers 5130-5131 (2 byte string)
    )
    # BMS warning and protection config

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
        # Set the current limits, populate cell count, etc
        # Return True if success, False for failure
        self.max_battery_charge_current = utils.MAX_BATTERY_CHARGE_CURRENT
        self.max_battery_discharge_current = utils.MAX_BATTERY_DISCHARGE_CURRENT

        self.max_battery_voltage = utils.MAX_CELL_VOLTAGE * self.cell_count
        self.min_battery_voltage = utils.MIN_CELL_VOLTAGE * self.cell_count
        return True

    def refresh_data(self):
        # call all functions that will refresh the battery data.
        # This will be called for every iteration (1 second)
        # Return True if success, False for failure
        result = self.read_soc_data()
        result = result and self.read_cell_data()
        result = result and self.read_temp_data()

        return result

    def read_gen_data(self):
        model = self.read_serial_data_renogy(self.command_model)
        # check if connection success
        if model is False:
            return False
        # may contain null bytes that we don't want
        model_num, _, _ = unpack("16s", model)[0].decode("utf-8").partition("\0")

        manufacturer = self.read_serial_data_renogy(self.command_manufacturer)
        if manufacturer is False:
            self.hardware_version = model_num
        else:
            # may contain null bytes that we don't want
            manufacturer, _, _ = (
                unpack("16s", manufacturer)[0].decode("utf-8").partition("\0")
            )
            self.hardware_version = f"{manufacturer} {model_num}"

        logger.info(self.hardware_version)

        # TODO: This isn't really accurate I think.
        self.temp_sensors = 2

        if self.cell_count is None:
            cc = self.read_serial_data_renogy(self.command_cell_count)
            self.cell_count = struct.unpack(">H", cc)[0]

            for c in range(self.cell_count):
                self.cells.append(Cell(False))

        firmware = self.read_serial_data_renogy(self.command_firmware_version)
        firmware_major, firmware_minor = unpack_from("2s2s", firmware)
        firmware_major = firmware_major.decode("utf-8")
        firmware_minor = firmware_minor.decode("utf-8")
        self.version = float(f"{firmware_major}.{firmware_minor}")

        capacity = self.read_serial_data_renogy(self.command_capacity)
        self.capacity = unpack(">L", capacity)[0] / 1000.0

        return True

    def read_soc_data(self):
        soc_data = self.read_serial_data_renogy(self.command_soc)
        # check if connection success
        if soc_data is False:
            return False

        current, voltage, capacity_remain = unpack_from(">hhL", soc_data)
        self.capacity_remain = capacity_remain / 1000.0
        self.current = current / 100.0
        self.voltage = voltage / 10.0
        self.soc = (self.capacity_remain / self.capacity) * 100
        return True

    def read_cell_data(self):
        cell_volt_data = self.read_serial_data_renogy(self.command_cell_voltages)
        cell_temp_data = self.read_serial_data_renogy(self.command_cell_temps)
        for c in range(self.cell_count):
            try:
                cell_volts = unpack_from(">H", cell_volt_data, c * 2)
                cell_temp = unpack_from(">H", cell_temp_data, c * 2)
                if len(cell_volts) != 0:
                    self.cells[c].voltage = cell_volts[0] / 10
                    self.cells[c].temp = cell_temp[0] / 10
            except struct.error:
                self.cells[c].voltage = 0
        return True

    def read_temp_data(self):
        # Check to see how many Enviromental Temp Sensors this battery has, it may have none.
        num_env_temps = self.read_serial_data_renogy(self.command_env_temp_count)
        logger.info("Number of Enviromental Sensors = %s", num_env_temps)

        if num_env_temps == 0:
            return False

        if num_env_temps == 1:
            temp1 = self.read_serial_data_renogy(self.command_env_temp1)

        if temp1 is False:
            return False
        else:
            self.temp1 = unpack(">H", temp1)[0] / 10
            logger.info("temp1 = %s °C", temp1)

        if num_env_temps == 2:
            temp2 = self.read_serial_data_renogy(self.command_env_temp2)

        if temp2 is False:
            return False
        else:
            self.temp2 = unpack(">H", temp2)[0] / 10
            logger.info("temp2 = %s °C", temp2)

        return True

    def read_bms_config(self):
        return True

    def calc_crc(self, data):
        crc = 0xFFFF
        for pos in data:
            crc ^= pos
            for i in range(8):
                if (crc & 1) != 0:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        return struct.pack("<H", crc)

    def generate_command(self, command):
        buffer = bytearray(self.command_address)
        buffer += self.command_read
        buffer += command
        buffer += self.calc_crc(buffer)

        return buffer

    def read_serial_data_renogy(self, command):
        # use the read_serial_data() function to read the data and then do BMS spesific checks (crc, start bytes, etc)
        data = read_serial_data(
            self.generate_command(command),
            self.port,
            self.baud_rate,
            self.LENGTH_POS,
            self.LENGTH_CHECK,
        )
        if data is False:
            return False

        start, flag, length = unpack_from("BBB", data)
        # checksum = unpack_from(">H", data, length + 3)

        if flag == 3:
            return data[3 : length + 3]
        else:
            logger.error(">>> ERROR: Incorrect Reply")
            return False
