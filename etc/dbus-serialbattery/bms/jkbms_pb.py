# -*- coding: utf-8 -*-

# Notes
# Added by https://github.com/KoljaWindeler

from battery import Battery, Cell
from utils import read_serial_data, logger
import utils
from struct import unpack_from
import sys


class Jkbms_pb(Battery):
    def __init__(self, port, baud, address):
        super(Jkbms_pb, self).__init__(port, baud, address)
        self.type = self.BATTERYTYPE
        self.unique_identifier_tmp = ""
        self.cell_count = 0
        self.address = address

    BATTERYTYPE = "JKBMS PB Model"
    LENGTH_CHECK = 0  # ignored
    LENGTH_POS = 2  # ignored
    LENGTH_SIZE = "H"  # ignored

    @property
    def command_status(self):
        return self.address + b"\x10\x16\x20\x00\x01\x02\x00\x00\xD6\xF1"

    @property
    def command_settings(self):
        return self.address + b"\x10\x16\x1E\x00\x01\x02\x00\x00\xD2\x2F"

    @property
    def command_about(self):
        return self.address + b"\x10\x16\x1C\x00\x01\x02\x00\x00\xD3\xCD"

    def test_connection(self):
        # call a function that will connect to the battery, send a command and retrieve the result.
        # The result or call should be unique to this BMS. Battery name or version, etc.
        # Return True if success, False for failure
        result = False
        try:
            result = self.get_settings()
            result = result and self.read_status_data()
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
            result = False

        return result

    def get_settings(self):
        # After successful  connection get_settings will be call to set up the battery.
        # Set the current limits, populate cell count, etc
        # Return True if success, False for failure
        status_data = self.read_serial_data_jkbms_pb(self.command_settings, 300)
        if status_data is False:
            return False

        VolSmartSleep = unpack_from("<i", status_data, 6)[0] / 1000
        VolCellUV = unpack_from("<i", status_data, 10)[0] / 1000
        VolCellUVPR = unpack_from("<i", status_data, 14)[0] / 1000
        VolCellOV = unpack_from("<i", status_data, 18)[0] / 1000
        VolCellOVPR = unpack_from("<i", status_data, 22)[0] / 1000
        VolBalanTrig = unpack_from("<i", status_data, 26)[0] / 1000
        VolSOC_full = unpack_from("<i", status_data, 30)[0] / 1000
        VolSOC_empty = unpack_from("<i", status_data, 34)[0] / 1000
        VolSysPwrOff = unpack_from("<i", status_data, 46)[0] / 1000
        CurBatCOC = unpack_from("<i", status_data, 50)[0] / 1000
        TIMBatCOCPDly = unpack_from("<i", status_data, 54)[0]
        TIMBatCOCPRDly = unpack_from("<i", status_data, 58)[0]
        CurBatDcOC = unpack_from("<i", status_data, 62)[0] / 1000
        TIMBatDcOCPDly = unpack_from("<i", status_data, 66)[0]
        TIMBatDcOCPRDly = unpack_from("<i", status_data, 70)[0]
        TIMBatSCPRDly = unpack_from("<i", status_data, 74)[0]
        CurBalanMax = unpack_from("<i", status_data, 78)[0] / 1000
        TMPBatCOT = unpack_from("<I", status_data, 82)[0] / 10
        TMPBatCOTPR = unpack_from("<I", status_data, 96)[0] / 10
        TMPBatDcOT = unpack_from("<I", status_data, 90)[0] / 10
        TMPBatDcOTPR = unpack_from("<I", status_data, 94)[0] / 10
        TMPBatCUT = unpack_from("<I", status_data, 98)[0] / 10
        TMPBatCUTPR = unpack_from("<I", status_data, 102)[0] / 10
        TMPMosOT = unpack_from("<I", status_data, 106)[0] / 10
        TMPMosOTPR = unpack_from("<I", status_data, 110)[0] / 10
        CellCount = unpack_from("<i", status_data, 114)[0]
        BatChargeEN = unpack_from("<i", status_data, 118)[0]
        BatDisChargeEN = unpack_from("<i", status_data, 122)[0]
        BalanEN = unpack_from("<i", status_data, 126)[0]
        CapBatCell = unpack_from("<i", status_data, 130)[0] / 1000
        SCPDelay = unpack_from("<i", status_data, 134)[0]

        # count of all cells in pack
        self.cell_count = CellCount

        # total Capaity in Ah
        self.capacity = CapBatCell

        # Continued discharge current
        self.max_battery_discharge_current = CurBatDcOC

        # Continued charge current
        self.max_battery_charge_current = CurBatCOC

        logger.debug("VolSmartSleep: " + str(VolSmartSleep))
        logger.debug("VolCellUV: " + str(VolCellUV))
        logger.debug("VolCellUVPR: " + str(VolCellUVPR))
        logger.debug("VolCellOV: " + str(VolCellOV))
        logger.debug("VolCellOVPR: " + str(VolCellOVPR))
        logger.debug("VolBalanTrig: " + str(VolBalanTrig))
        logger.debug("VolBalanTrig: " + str(VolBalanTrig))
        logger.debug("VolSOC_full: " + str(VolSOC_full))
        logger.debug("VolSOC_empty: " + str(VolSOC_empty))
        logger.debug("VolSysPwrOff: " + str(VolSysPwrOff))
        logger.debug("CurBatCOC: " + str(CurBatCOC))
        logger.debug("TIMBatCOCPDly: " + str(TIMBatCOCPDly))
        logger.debug("TIMBatCOCPRDly: " + str(TIMBatCOCPRDly))
        logger.debug("CurBatDcOC: " + str(CurBatDcOC))
        logger.debug("TIMBatDcOCPDly: " + str(TIMBatDcOCPDly))
        logger.debug("TIMBatDcOCPRDly: " + str(TIMBatDcOCPRDly))
        logger.debug("TIMBatSCPRDly: " + str(TIMBatSCPRDly))
        logger.debug("CurBalanMax: " + str(CurBalanMax))
        logger.debug("TMPBatCOT: " + str(TMPBatCOT))
        logger.debug("TMPBatCOTPR: " + str(TMPBatCOTPR))
        logger.debug("TMPBatDcOT: " + str(TMPBatDcOT))
        logger.debug("TMPBatDcOTPR: " + str(TMPBatDcOTPR))
        logger.debug("TMPBatCUT: " + str(TMPBatCUT))
        logger.debug("TMPBatCUTPR: " + str(TMPBatCUTPR))
        logger.debug("TMPMosOT: " + str(TMPMosOT))
        logger.debug("TMPMosOTPR: " + str(TMPMosOTPR))
        logger.debug("CellCount: " + str(CellCount))
        logger.debug("BatChargeEN: " + str(BatChargeEN))
        logger.debug("BatDisChargeEN: " + str(BatDisChargeEN))
        logger.debug("BalanEN: " + str(BalanEN))
        logger.debug("CapBatCell: " + str(CapBatCell))
        logger.debug("SCPDelay: " + str(SCPDelay))

        status_data = self.read_serial_data_jkbms_pb(self.command_about, 300)
        serial_nr = status_data[86:96].decode("utf-8")
        vendor_id = status_data[6:18].decode("utf-8")
        hw_version = (
            status_data[22:26].decode("utf-8")
            + " / "
            + status_data[30:34].decode("utf-8")
        )
        sw_version = status_data[30:34].decode("utf-8")  # will be overridden

        self.unique_identifier_tmp = serial_nr
        self.version = sw_version
        self.hardware_version = hw_version

        logger.debug("Serial Nr: " + str(serial_nr))
        logger.debug("Vendor ID: " + str(vendor_id))
        logger.debug("HW Version: " + str(hw_version))
        logger.debug("SW Version: " + str(sw_version))

        self.max_battery_voltage = utils.MAX_CELL_VOLTAGE * self.cell_count
        self.min_battery_voltage = utils.MIN_CELL_VOLTAGE * self.cell_count

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

    def read_status_data(self):
        status_data = self.read_serial_data_jkbms_pb(self.command_status, 299)
        # check if connection success
        if status_data is False:
            return False

        #        logger.error("sucess we have data")
        #        be = ''.join(format(x, ' 02X') for x in status_data)
        #        logger.error(be)

        # cell voltages
        for c in range(self.cell_count):
            if (unpack_from("<H", status_data, c * 2 + 6)[0] / 1000) != 0:
                self.cells[c].voltage = (
                    unpack_from("<H", status_data, c * 2 + 6)[0] / 1000
                )

        # MOSFET temperature
        temp_mos = unpack_from("<h", status_data, 144)[0] / 10
        self.to_temp(0, temp_mos if temp_mos < 99 else (100 - temp_mos))

        # Temperature sensors
        temp1 = unpack_from("<h", status_data, 162)[0] / 10
        temp2 = unpack_from("<h", status_data, 164)[0] / 10
        self.to_temp(1, temp1 if temp1 < 99 else (100 - temp1))
        self.to_temp(2, temp2 if temp2 < 99 else (100 - temp2))

        # Battery voltage
        self.voltage = unpack_from("<I", status_data, 150)[0] / 1000

        # Battery ampere
        self.current = unpack_from("<i", status_data, 158)[0] / 1000

        # SOC
        self.soc = unpack_from("<B", status_data, 173)[0]

        # cycles
        self.cycles = unpack_from("<i", status_data, 182)[0]

        # capacity
        self.capacity_remain = unpack_from("<i", status_data, 174)[0] / 1000

        # fuses
        self.to_protection_bits(unpack_from("<I", status_data, 166)[0])

        # bits
        bal = unpack_from("<B", status_data, 172)[0]
        charge = unpack_from("<B", status_data, 198)[0]
        discharge = unpack_from("<B", status_data, 199)[0]
        self.charge_fet = 1 if charge != 0 else 0
        self.discharge_fet = 1 if discharge != 0 else 0
        self.balancing = 1 if bal != 0 else 0

        # show wich cells are balancing
        if self.get_min_cell() is not None and self.get_max_cell() is not None:
            for c in range(self.cell_count):
                if self.balancing and (
                    self.get_min_cell() == c or self.get_max_cell() == c
                ):
                    self.cells[c].balance = True
                else:
                    self.cells[c].balance = False

        # logging
        """
        for c in range(self.cell_count):
                logger.error("Cell "+str(c)+" voltage: "+str(self.cells[c].voltage)+"V")
        logger.error("Temp 2: "+str(temp1))
        logger.error("Temp 3: "+str(temp2))
        logger.error("voltage: "+str(self.voltage)+"V")
        logger.error("Current: "+str(self.current))
        logger.error("SOC: "+str(self.soc)+"%")
        logger.error("Mos Temperature: "+str(temp_mos))
        """

        return True

    def unique_identifier(self) -> str:
        """
        Used to identify a BMS when multiple BMS are connected
        """
        return self.unique_identifier_tmp

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
        Bit 0x00000001: Wire resistance alarm: 1 warning only, 0 nomal -> OK
        Bit 0x00000002: MOS overtemperature alarm: 1 alarm, 0 nomal -> OK
        Bit 0x00000004: Cell quantity alarm: 1 alarm, 0 nomal -> OK
        Bit 0x00000008: Current sensor error alarm: 1 alarm, 0 nomal -> OK
        Bit 0x00000010: Cell OVP alarm: 1 alarm, 0 nomal -> OK
        Bit 0x00000020: Bat OVP alarm: 1 alarm, 0 nomal -> OK
        Bit 0x00000040: Charge Over current alarm: 1 alarm, 0 nomal -> OK
        Bit 0x00000080: Charge SCP alarm: 1 alarm, 0 nomal -> OK
        Bit 0x00000100: Charge OTP: 1 alarm, 0 nomal -> OK
        Bit 0x00000200: Charge UTP: 1 alarm, 0 nomal -> OK
        Bit 0x00000400: CPU Aux Communication: 1 alarm, 0 nomal -> OK
        Bit 0x00000800: Cell UVP: 1 alarm, 0 nomal -> OK
        Bit 0x00001000: Batt UVP: 1 alarm, 0 nomal
        Bit 0x00002000: Discharge Over current: 1 alarm, 0 nomal
        Bit 0x00004000: Discharge SCP: 1 alarm, 0 nomal
        Bit 0x00008000: Discharge OTP: 1 alarm, 0 nomal
        Bit 0x00010000: Charge MOS: 1 alarm, 0 nomal
        Bit 0x00020000: Discharge MOS: 1 alarm, 0 nomal
        Bit 0x00040000: GPS disconnected: 1 alarm, 0 nomal
        Bit 0x00080000: Modify PWD in time: 1 alarm, 0 nomal
        Bit 0x00100000: Discharg on Faied: 1 alarm, 0 nomal
        Bit 0x00200000: Battery over Temp: 1 alarm, 0 nomal
        """

        # low capacity alarm
        self.protection.soc_low = (byte_data & 0x00001000) * 2
        # MOSFET temperature alarm
        self.protection.temp_high_internal = (byte_data & 0x00000002) * 2
        # charge over voltage alarm
        self.protection.voltage_high = (byte_data & 0x00000020) * 2
        # discharge under voltage alarm
        self.protection.voltage_low = (byte_data & 0x00000800) * 2
        # charge overcurrent alarm
        self.protection.current_over = (byte_data & 0x00000040) * 2
        # discharge over current alarm
        self.protection.current_under = (byte_data & 0x00002000) * 2
        # core differential pressure alarm OR unit overvoltage alarm
        self.protection.cell_imbalance = 0
        # unit undervoltage alarm
        self.protection.voltage_cell_low = (byte_data & 0x00001000) * 2
        # battery overtemperature alarm OR overtemperature alarm in the battery box
        self.protection.temp_high_charge = (byte_data & 0x00000100) * 2
        self.protection.temp_low_charge = (byte_data & 0x00000200) * 2
        # check if low/high temp alarm arise during discharging
        self.protection.temp_high_discharge = (byte_data & 0x00008000) * 2
        self.protection.temp_low_discharge = 0

    def read_serial_data_jkbms_pb(self, command: str, length: int) -> bool:
        """
        use the read_serial_data() function to read the data and then do BMS specific checks (crc, start bytes, etc)
        :param command: the command to be sent to the bms
        :return: True if everything is fine, else False
        """
        data = read_serial_data(
            command,
            self.port,
            self.baud_rate,
            self.LENGTH_POS,  # ignored
            self.LENGTH_CHECK,  # ignored
            length,
            self.LENGTH_SIZE,  # ignored
        )
        if data is False:
            return False

        # be = ''.join(format(x, ' 02X') for x in data)
        # logger.error(be)

        # I never understood the CRC algorithm in the message,
        # so we check the header and the length and that's it

        if data[0] == 0x55 and data[1] == 0xAA:
            return data
        else:
            logger.error(">>> ERROR: Incorrect Reply ")
            return False
