# -*- coding: utf-8 -*-
from battery import Protection, Battery, Cell
from utils import is_bit_set, read_serial_data, logger
import utils
from struct import unpack_from


class BatteryTemplate(Battery):
    def __init__(self, port, baud, address):
        super(BatteryTemplate, self).__init__(port, baud, address)
        self.type = self.BATTERYTYPE

    BATTERYTYPE = "Template"
    LENGTH_CHECK = 4
    LENGTH_POS = 3

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

        # Uncomment if BMS does not supply capacity
        # self.capacity = BATTERY_CAPACITY
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

        return result

    def read_status_data(self):
        status_data = self.read_serial_data_template(self.command_status)
        # check if connection success
        if status_data is False:
            return False

        (
            self.cell_count,
            self.temp_sensors,
            self.charger_connected,
            self.load_connected,
            state,
            self.cycles,
        ) = unpack_from(">bb??bhx", status_data)

        self.hardware_version = "TemplateBMS " + str(self.cell_count) + " cells"
        logger.info(self.hardware_version)
        return True

    def read_soc_data(self):
        soc_data = self.read_serial_data_template(self.command_soc)
        # check if connection success
        if soc_data is False:
            return False

        voltage, current, soc = unpack_from(">hxxhh", soc_data)
        self.voltage = voltage / 10
        self.current = current / -10
        self.soc = soc / 10
        return True

    def read_serial_data_template(self, command):
        # use the read_serial_data() function to read the data and then do BMS spesific checks (crc, start bytes, etc)
        data = read_serial_data(
            command, self.port, self.baud_rate, self.LENGTH_POS, self.LENGTH_CHECK
        )
        if data is False:
            return False

        start, flag, command_ret, length = unpack_from("BBBB", data)
        checksum = sum(data[:-1]) & 0xFF

        if start == 165 and length == 8 and checksum == data[12]:
            return data[4 : length + 4]
        else:
            logger.error(">>> ERROR: Incorrect Reply")
            return False
