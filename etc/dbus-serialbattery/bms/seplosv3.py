# -*- coding: utf-8 -*-

import math
import struct
from typing import Dict, Union

import minimalmodbus
import serial
from battery import Battery, Cell, Protection
from utils import logger

RETRYCNT = 3


class Seplosv3(Battery):
    def __init__(self, port, baud, address):
        super(Seplosv3, self).__init__(port, baud, address)
        self.type = "Seplosv3_BMS_modbus"
        self.serialnumber = ""
        self.mbdev: Union[minimalmodbus.Instrument, None] = None
        if address is not None and len(address) > 0:
            self.slaveaddress: int = int(address)
            self.slaveaddresses: list[int] = [self.slaveaddress]
        else:
            self.slaveaddress: int = 0
            self.slaveaddresses = list(range(16))

    def get_modbus(self, slaveaddress=0) -> minimalmodbus.Instrument:
        if self.mbdev is not None and slaveaddress == self.slaveaddress:
            return self.mbdev

        # hack to allow communication to the Seplos BMS using minimodbus which uses slaveaddress 0 as broadcast
        if slaveaddress == 0:
            minimalmodbus._SLAVEADDRESS_BROADCAST = 0xF0
        else:
            minimalmodbus._SLAVEADDRESS_BROADCAST = 0

        mbdev = minimalmodbus.Instrument(
            self.port,
            slaveaddress=slaveaddress,
            mode="rtu",
            close_port_after_each_call=True,
            debug=False,
        )
        mbdev.serial.parity = minimalmodbus.serial.PARITY_NONE
        mbdev.serial.stopbits = serial.STOPBITS_ONE
        mbdev.serial.baudrate = 19200
        mbdev.serial.timeout = 0.4
        return mbdev

    def test_connection(self):
        # call a function that will connect to the battery, send a command and retrieve the result.
        # The result or call should be unique to this BMS. Battery name or version, etc.
        # Return True if success, False for failure

        # This will cycle trhough all the slave addresses to find the BMS.
        for self.slaveaddress in self.slaveaddresses:
            mbdev = self.get_modbus(self.slaveaddress)
            logger.info(
                f"Start testing for Seplos v3 on slave address {self.slaveaddress}"
            )

            for n in range(1, RETRYCNT):
                try:
                    factory = mbdev.read_string(
                        registeraddress=0x1700, number_of_registers=10, functioncode=4
                    )
                    if "XZH-ElecTech Co.,Ltd" in factory:
                        logger.info(
                            f"Identified Seplos v3 by '{factory}' on slave address {self.slaveaddress}"
                        )
                        model = mbdev.read_string(
                            registeraddress=0x170A,
                            number_of_registers=10,
                            functioncode=4,
                        )
                        logger.info(f"Model: {model}")
                        self.model = model.rstrip("\x00")
                        self.hardware_version = model.rstrip("\x00")

                        sn = mbdev.read_string(
                            registeraddress=0x1715,
                            number_of_registers=15,
                            functioncode=4,
                        )
                        self.serialnumber = sn.rstrip("\x00")
                        logger.info(f"Serial nr: {self.serialnumber}")

                        sw_version = mbdev.read_string(
                            registeraddress=0x1714,
                            number_of_registers=1,
                            functioncode=4,
                        )
                        sw_version = sw_version.rstrip("\x00")
                        self.version = sw_version[0] + "." + sw_version[1]
                        logger.info(f"Firmware Version: {self.version}")
                        found = True
                        self.mbdev = mbdev

                except Exception as e:
                    logger.debug(
                        f"Seplos v3 testing failed ({e}) {n}/{RETRYCNT} for {self.port}({str(self.slaveaddress)})"
                    )
                    continue
                break
            if found:
                self.type = f"{self.hardware_version}"
                break

        # give the user a feedback that no BMS was found
        if not found:
            logger.error(">>> ERROR: No Seplos v3 found - returning")

        return found

    def unique_identifier(self) -> str:
        """
        Used to identify a BMS when multiple BMS are connected
        Provide a unique identifier from the BMS to identify a BMS, if multiple same BMS are connected
        e.g. the serial number
        If there is no such value, please remove this function
        """
        return self.serialnumber

    def get_settings(self):
        # After successful  connection get_settings will be call to set up the battery.
        # Set the current limits, populate cell count, etc
        # Return True if success, False for failure

        # Values:  battery_type, version, hardware_version, min_battery_voltage, max_battery_voltage,
        # MAX_BATTERY_CHARGE_CURRENT, MAX_BATTERY_DISCHARGE_CURRENT, cell_count, capacity

        self.battery_type = "LiFePO4"
        self.charger_connected = True
        self.load_connected = True
        return self.refresh_data()

    def read_device_date(self):
        try:
            mb = self.get_modbus(self.slaveaddress)
            spa = mb.read_registers(
                registeraddress=0x1300, number_of_registers=0x6A, functioncode=4
            )
            pia = mb.read_registers(
                registeraddress=0x1000, number_of_registers=0x12, functioncode=4
            )
            pib = mb.read_registers(
                registeraddress=0x1100, number_of_registers=0x1A, functioncode=4
            )
            sca = mb.read_registers(
                registeraddress=0x1500, number_of_registers=0x04, functioncode=4
            )
            pic = mb.read_bits(0x1200, number_of_bits=0x90, functioncode=1)
            sfa = mb.read_bits(0x1400, number_of_bits=0x50, functioncode=1)
            logger.debug(f"spa: {spa}")
            logger.debug(f"pia: {pia}")
            logger.debug(f"pib: {pib}")
            logger.debug(f"sca: {sca}")
            logger.debug(f"sfa: {sfa}")
            logger.debug(f"pic: {pic}")
        except Exception as e:
            logger.info(f"Error getting data {e}")
            USE_MOCK = False
            if USE_MOCK:
                # fmt: off
                logger.warning(f"Using Mock data")
                spa = [4, 16, 5400, 5600, 5400, 5760, 4800, 4640, 4800, 4320, 3400, 3500, 3400, 3650, 3100, 2900, 3100, 2700, 2000, 1000, 500, 203, 205, 210, 100, 300, 300, 65333, 65331, 65326, 100, 65186, 300, 65236, 106, 600, 5, 3000, 205, 10, 3500, 3400, 1500, 1000, 800, 200, 30, 3201, 3231, 3231, 3281, 2781, 2751, 2731, 2631, 3231, 3281, 3281, 3331, 2761, 2631, 2731, 2581, 3201, 3231, 3281, 3331, 2761, 2731, 2731, 2631, 3581, 3681, 3581, 3831, 2831, 2731, 3231, 2731, 10, 3400, 50, 30, 960, 150, 100, 70, 50, 30400, 30400, 3800, 48, 60, 240, 10, 7, 0, 13, 0, 500, 300, 5760, 180, 65356, 5, 8]
                pia = [5236, 1301, 3800, 30400, 64, 125, 1000, 2, 3272, 2837, 3275, 3268, 2845, 2831, 0, 180, 180, 1000]
                pib = [0,0x0,0x0,0x0,0x1,0x0,0x0,0x1,0x1,0x1,0x0,0x1,0x0,0x1,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x1,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x1,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x1,0x0,0x0,0x0,0x0,0x0,0x1,0x1,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0]
                sca = [59399, 776, 4141, 7710]
                sfa = [1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0]
                pic = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                # fmt: on
            else:
                return None, None, None, None, None, None
        return spa, pia, pib, sca, pic, sfa

    @staticmethod
    def to_signed_int(value):
        """
        Converts an unsigned value to a signed value.
        Args:
            value (int): The unsigned value to be converted.
        Returns:
            int: The signed value.
        """
        packval = struct.pack("<H", value)
        return struct.unpack("<h", packval)[0]

    def update_cells(self, pib) -> bool:
        try:
            self.cells = []
            for i in range(0, self.cell_count):
                cell = Cell(False)
                cell.voltage = pib[i] / 1000.0
                cell.temp = pib[0x10 + math.floor(i / 4)] / 10 - 273.0
                self.cells.append(cell)
            self.temp1 = pib[0x10] / 10 - 273.0
            self.temp2 = pib[0x11] / 10 - 273.0
            self.temp3 = pib[0x12] / 10 - 273.0
            self.temp4 = pib[0x13] / 10 - 273.0
            self.temp_mos = pib[0x19] / 10 - 273.0
        except Exception as e:
            logger.info(f"Error updating cells {e}")
            return False
        return True

    def update_pack_info(self, pia) -> bool:
        try:
            self.voltage = pia[0] / 100
            self.current = self.to_signed_int(pia[1]) / 100
            self.capacity_remain = pia[2] / 100  # check if this is from pia or from spa
            #        self.capacity = pia[2]/100    # check if this is from pia or from spa
            self.soc = pia[5] / 10
            self.total_ah_drawn = pia[4] * 10
            self.cycles = pia[7]
            self.max_battery_discharge_current = pia[0x0F]
            self.max_battery_charge_current = pia[0x10]
        except Exception as e:
            logger.info(f"Error updating pack info {e}")
            return False
        return True

        # These fields most likely not expected to be set by a BMS implementation
        # self.production = None
        # self.allow_max_voltage: bool = True  # save state to preserve on restart
        # self.charge_mode: str = None
        # self.charge_mode_debug: str = ""
        # self.charge_limitation: str = None
        # self.discharge_limitation: str = None
        # self.linear_cvl_last_set: int = 0
        # self.linear_ccl_last_set: int = 0
        # self.linear_dcl_last_set: int = 0

        # These fields to be checked f they need to be set by a BMS implementation
        # self.control_voltage: float = None
        # self.control_discharge_current: int = None
        # self.control_charge_current: int = None
        # self.control_allow_charge: bool = None
        # self.control_allow_discharge: bool = None

    def update_sysinfo(self, spa) -> bool:
        try:
            self.temp_sensors = spa[0x00]
            self.cell_count = spa[1]
            self.capacity = spa[0x59] / 100
            # self.capacity_remain = spa[0x5A] / 100
            self.max_battery_voltage = spa[0x05] / 100
            self.min_battery_voltage = spa[0x11] / 100
            self.control_voltage = spa[0x65] / 100
            self.control_charge_current = spa[0x66]
            self.control_discharge_current = spa[0x67]
        except Exception as e:
            logger.info(f"Error updating sys info {e}")
            return False
        return True

    def update_alarms(self, sfa) -> bool:
        try:
            self.protection = Protection()
            #   ALARM = 2 , WARNING = 1 , OK = 0
            self.protection.voltage_high = (
                2 if sfa[0x05] == 0 else 1 if sfa[0x04] == 0 else 0
            )
            self.protection.voltage_low = (
                2 if sfa[0x06] == 0 else 1 if sfa[0x06] == 0 else 0
            )
            # self.protection.voltage_cell_high =  1 if  sfa[0x00] == 0 else 0 + 1 if  sfa[0x01] == 0 else 0
            self.protection.voltage_cell_low = (
                2 if sfa[0x03] == 0 else 1 if sfa[0x02] == 0 else 0
            )
            self.protection.soc_low = 2 if sfa[0x30] == 0 else 0
            self.protection.current_over = (
                2 if sfa[0x21] == 0 else 1 if sfa[0x20] == 0 else 0
            )
            self.protection.current_under = (
                2 if sfa[0x24] == 0 else 1 if sfa[0x23] == 0 else 0
            )
            # self.protection.cell_imbalance = 2 if  sfa[0x4c] == 0 else 0   # Need to doiuble check logic as this is set unexpectedly
            # set by pic 0x74 --> validated in seplos UI
            self.protection.internal_failure = (
                2
                if (sfa[0x48] + sfa[0x49] + sfa[0x4A] + sfa[0x4B] + sfa[0x4D] + sfa[53])
                < 5
                else 0
            )
            self.protection.temp_high_charge = (
                2 if sfa[0x09] == 0 else 1 if sfa[0x08] == 0 else 0
            )
            self.protection.temp_low_charge = (
                2 if sfa[0x0B] == 0 else 1 if sfa[0x0A] == 0 else 0
            )
            self.protection.temp_high_discharge = (
                2 if sfa[0x0D] == 0 else 1 if sfa[0x0C] == 0 else 0
            )
            self.protection.temp_low_discharge = (
                2 if sfa[0x0F] == 0 else 1 if sfa[0x0E] == 0 else 0
            )
            self.protection.temp_high_internal = (
                2 if sfa[0x15] == 0 else 1 if sfa[0x14] == 0 else 0
            )
        except Exception as e:
            logger.info(f"Error updating alarm info {e}")
            return False
        return True

    def update_system_control(self, pic, sca) -> bool:
        try:
            self.discharge_fet = True if pic[0x78] == 1 else False
            self.charge_fet = True if pic[0x79] == 1 else False
            self.balance_fet = True if pic[0x80] == 1 else False
            self.protection.cell_imbalance = 2 if pic[0x74] == 0 else 0
        except Exception as e:
            logger.info(f"Error updating fets {e}")
            return False
        return True

    def refresh_data(self) -> bool:
        # call all functions that will refresh the battery data.
        # This will be called for every iteration (1 second)
        # Return True if success, False for failure
        spa, pia, pib, sca, pic, sfa = self.read_device_date()
        results = []
        if spa is None:
            results.append(False)
        else:
            results.append(self.update_sysinfo(spa))

        if pia is None:
            results.append(False)
        else:
            results.append(self.update_pack_info(pia))

        if pib is None:
            results.append(False)
        else:
            results.append(self.update_cells(pib))

        if sca is None or pic is None:
            results.append(False)
        else:
            results.append(self.update_system_control(pic, sca))
            pass

        if sfa is None:
            results.append(False)
        else:
            results.append(self.update_alarms(sfa))

        for result in results:
            if result is False:
                logger.info(
                    f"Updating Seplos v3 {self.hardware_version} {self.serialnumber} failed: {results}"
                )
                return False
        logger.info(f"Updating Seplos v3 {self.hardware_version} {self.serialnumber}")
        return True
