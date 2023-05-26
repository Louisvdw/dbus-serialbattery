# -*- coding: utf-8 -*-
# known limitations:
#   - only BMS variants with 2 cell temperature sensors supported
#   - some "interesting" datapoints are not read (e. g. registers 52: switch type, 62: bootloader and firmware version)
#   - SOC not yet resettable from Venus (similary to Daly for support of writing SOC), but modbus write to 120 should be
#     fairly possible)


from battery import Battery, Cell
from utils import logger
import utils
import serial
import time
import minimalmodbus
from typing import Dict
import threading

# the Heltec BMS is not always as responsive as it should, so let's try it up to (RETRYCNT - 1) times to talk to it
RETRYCNT = 10

# the wait time after a communication - normally this should be as defined by modbus RTU and handled in minimalmodbus,
# but yeah, it seems we need it for the Heltec BMS
SLPTIME = 0.03

mbdevs: Dict[int, minimalmodbus.Instrument] = {}
locks: Dict[int, any] = {}


class HeltecModbus(Battery):
    def __init__(self, port, baud, address):
        super(HeltecModbus, self).__init__(port, baud, address)
        self.type = "Heltec_Smart"

    def test_connection(self):
        # call a function that will connect to the battery, send a command and retrieve the result.
        # The result or call should be unique to this BMS. Battery name or version, etc.
        # Return True if success, False for failure
        for self.address in utils.HELTEC_MODBUS_ADDR:
            logger.info("Testing on slave address " + str(self.address))
            found = False
            if self.address not in locks:
                locks[self.address] = threading.Lock()

            # TODO: We need to lock not only based on the address, but based on the port as soon as multiple BMSs
            # are supported on the same serial interface. Then locking on the port will be enough.

            with locks[self.address]:
                mbdev = minimalmodbus.Instrument(
                    self.port,
                    slaveaddress=self.address,
                    mode="rtu",
                    close_port_after_each_call=True,
                    debug=False,
                )
                mbdev.serial.parity = minimalmodbus.serial.PARITY_NONE
                mbdev.serial.stopbits = serial.STOPBITS_ONE
                mbdev.serial.baudrate = 9600
                # yes, 400ms is long but the BMS is sometimes really slow in responding, so this is a good compromise
                mbdev.serial.timeout = 0.4
                mbdevs[self.address] = mbdev

                for n in range(1, RETRYCNT):
                    try:
                        string = mbdev.read_string(7, 13)
                        time.sleep(SLPTIME)
                        found = True
                        logger.info(
                            "found in try "
                            + str(n)
                            + "/"
                            + str(RETRYCNT)
                            + " for "
                            + self.port
                            + "("
                            + str(self.address)
                            + "): "
                            + string
                        )
                    except Exception as e:
                        logger.warn(
                            "testing failed ("
                            + str(e)
                            + ") "
                            + str(n)
                            + "/"
                            + str(RETRYCNT)
                            + " for "
                            + self.port
                            + "("
                            + str(self.address)
                            + ")"
                        )
                        continue
                    break
                if found:
                    self.type = "#" + str(self.address) + "_Heltec_Smart"
                    break

        return (
            found
            and self.read_status_data()
            and self.get_settings()
            and self.refresh_data()
        )

    def get_settings(self):
        self.max_battery_voltage = self.max_cell_voltage * self.cell_count
        self.min_battery_voltage = self.min_cell_voltage * self.cell_count

        return True

    def refresh_data(self):
        # call all functions that will refresh the battery data.
        # This will be called for every iteration (1 second)
        # Return True if success, False for failure
        return self.read_soc_data() and self.read_cell_data()

    def read_status_data(self):
        mbdev = mbdevs[self.address]

        with locks[self.address]:
            for n in range(1, RETRYCNT + 1):
                try:
                    ccur = mbdev.read_register(191, 0, 3, False)
                    self.max_battery_charge_current = (
                        (int)(((ccur & 0xFF) << 8) | ((ccur >> 8) & 0xFF))
                    ) / 100
                    time.sleep(SLPTIME)

                    dc = mbdev.read_register(194, 0, 3, False)
                    self.max_battery_discharge_current = (
                        ((dc & 0xFF) << 8) | ((dc >> 8) & 0xFF)
                    ) / 100
                    time.sleep(SLPTIME)

                    cap = mbdev.read_register(118, 0, 3, False)
                    self.capacity = (((cap & 0xFF) << 8) | ((cap >> 8) & 0xFF)) / 10
                    time.sleep(SLPTIME)

                    cap = mbdev.read_register(119, 0, 3, False)
                    self.actual_capacity = (
                        ((cap & 0xFF) << 8) | ((cap >> 8) & 0xFF)
                    ) / 10
                    time.sleep(SLPTIME)

                    cap = mbdev.read_register(126, 0, 3, False)
                    self.learned_capacity = (
                        ((cap & 0xFF) << 8) | ((cap >> 8) & 0xFF)
                    ) / 10
                    time.sleep(SLPTIME)

                    volt = mbdev.read_register(169, 0, 3, False)
                    self.max_cell_voltage = (
                        ((volt & 0xFF) << 8) | ((volt >> 8) & 0xFF)
                    ) / 1000
                    time.sleep(SLPTIME)

                    volt = mbdev.read_register(172, 0, 3, False)
                    self.min_cell_voltage = (
                        ((volt & 0xFF) << 8) | ((volt >> 8) & 0xFF)
                    ) / 1000
                    time.sleep(SLPTIME)

                    string = mbdev.read_string(7, 13)
                    self.hwTypeName = string
                    time.sleep(SLPTIME)

                    string = mbdev.read_string(41, 6)
                    self.devName = string
                    time.sleep(SLPTIME)

                    serial1 = mbdev.read_registers(2, number_of_registers=4)
                    self.unique_identifier = "-".join(
                        "{:04x}".format(x) for x in serial1
                    )
                    time.sleep(SLPTIME)

                    self.pw = mbdev.read_string(47, 2)
                    time.sleep(SLPTIME)

                    tmp = mbdev.read_register(75)
                    # h: batterytype: 0: Ternery Lithium, 1: Iron Lithium, 2: Lithium Titanat
                    # l: #of cells

                    self.cell_count = (tmp >> 8) & 0xFF
                    tmp = tmp & 0xFF
                    if tmp == 0:
                        self.cellType = "Ternary Lithium"
                    elif tmp == 1:
                        self.cellType = "Iron Lithium"
                    elif tmp == 2:
                        self.cellType = "Lithium Titatnate"
                    else:
                        self.cellType = "unknown"
                    time.sleep(SLPTIME)

                    self.hardware_version = (
                        self.devName
                        + "("
                        + str((mbdev.read_register(38) >> 8) & 0xFF)
                        + ")"
                    )
                    time.sleep(SLPTIME)

                    date = mbdev.read_long(39, 3, True, minimalmodbus.BYTEORDER_LITTLE)
                    self.production_date = (
                        str(date & 0xFFFF)
                        + "-"
                        + str((date >> 24) & 0xFF)
                        + "-"
                        + str((date >> 16) & 0xFF)
                    )
                    time.sleep(SLPTIME)

                    # we finished all readings without trouble, so let's break from the retry loop
                    break
                except Exception as e:
                    logger.warn(
                        "Error reading settings from BMS, retry ("
                        + str(n)
                        + "/"
                        + str(RETRYCNT)
                        + "): "
                        + str(e)
                    )
                    if n == RETRYCNT:
                        return False
                    continue

            logger.info(self.hardware_version)
            logger.info("Heltec-" + self.hwTypeName)
            logger.info("  Dev name: " + self.devName)
            logger.info("  Serial: " + self.unique_identifier)
            logger.info("  Made on: " + self.production_date)
            logger.info("  Cell count: " + str(self.cell_count))
            logger.info("  Cell type: " + self.cellType)
            logger.info("  BT password: " + self.pw)
            logger.info("  rated capacity: " + str(self.capacity))
            logger.info("  actual capacity: " + str(self.actual_capacity))
            logger.info("  learned capacity: " + str(self.learned_capacity))

        return True

    def read_soc_data(self):
        mbdev = mbdevs[self.address]

        with locks[self.address]:
            for n in range(1, RETRYCNT):
                try:
                    self.voltage = (
                        mbdev.read_long(76, 3, True, minimalmodbus.BYTEORDER_LITTLE)
                        / 1000
                    )
                    time.sleep(SLPTIME)

                    self.current = -(
                        mbdev.read_long(78, 3, True, minimalmodbus.BYTEORDER_LITTLE)
                        / 100
                    )
                    time.sleep(SLPTIME)

                    runState1 = mbdev.read_long(
                        152, 3, True, minimalmodbus.BYTEORDER_LITTLE
                    )
                    time.sleep(SLPTIME)

                    # bit 29 is discharge protection
                    if (runState1 & 0x20000000) == 0:
                        self.discharge_fet = True
                    else:
                        self.discharge_fet = False

                    # bit 28 is charge protection
                    if (runState1 & 0x10000000) == 0:
                        self.charge_fet = True
                    else:
                        self.charge_fet = False

                    warnings = mbdev.read_long(
                        156, 3, True, minimalmodbus.BYTEORDER_LITTLE
                    )
                    if (warnings & (1 << 3)) or (
                        warnings & (1 << 15)
                    ):  # 15 is full protection, 3 is total overvoltage
                        self.voltage_high = 2
                    else:
                        self.voltage_high = 0

                    if warnings & (1 << 0):
                        self.protection.voltage_cell_high = 2
                        # we handle a single cell OV as total OV, as long as cell_high is not explicitly handled
                        self.protection.voltage_high = 1
                    else:
                        self.protection.voltage_cell_high = 0

                    if warnings & (1 << 1):
                        self.protection.voltage_cell_low = 2
                    else:
                        self.protection.voltage_cell_low = 0

                    if warnings & (1 << 4):
                        self.protection.voltage_low = 2
                    else:
                        self.protection.voltage_low = 0

                    if warnings & (1 << 5):
                        self.protection.current_over = 2
                    else:
                        self.protection.current_over = 0

                    if warnings & (1 << 7):
                        self.protection.current_under = 2
                    elif warnings & (1 << 6):
                        self.protection.current_under = 1
                    else:
                        self.protection.current_under = 0

                    if warnings & (1 << 8):  # this is a short circuit
                        self.protection.current_over = 2

                    if warnings & (1 << 9):
                        self.protection.temp_high_charge = 2
                    else:
                        self.protection.temp_high_charge = 0

                    if warnings & (1 << 10):
                        self.protection.temp_low_charge = 2
                    else:
                        self.protection.temp_low_charge = 0

                    if warnings & (1 << 11):
                        self.protection.temp_high_discharge = 2
                    else:
                        self.protection.temp_high_discharge = 0

                    if warnings & (1 << 12):
                        self.protection.temp_low_discharge = 2
                    else:
                        self.protection.temp_low_discharge = 0

                    if warnings & (1 << 13):  # MOS overtemp
                        self.protection.temp_high_internal = 2
                    else:
                        self.protection.temp_high_internal = 0

                    if warnings & (1 << 14):  # SOC low
                        self.protection.soc_low = 2
                    else:
                        self.protection.soc_low = 0

                    if warnings & (0xFFFF0000):  # any other fault
                        self.protection.internal_failure = 2
                    else:
                        self.protection.internal_failure = 0

                    socsoh = mbdev.read_register(120, 0, 3, False)
                    self.soh = socsoh & 0xFF
                    self.soc = (socsoh >> 8) & 0xFF
                    time.sleep(SLPTIME)

                    # we could read min and max temperature, here, but I have a BMS with only 2 sensors,
                    # so I couldn't test the logic and read therefore only the first two temperatures
                    #   tminmax = mbdev.read_register(117, 0, 3, False)
                    #   nmin = (tminmax & 0xFF)
                    #   nmax = ((tminmax >> 8) & 0xFF)

                    temps = mbdev.read_register(113, 0, 3, False)
                    self.temp1 = (temps & 0xFF) - 40
                    self.temp2 = ((temps >> 8) & 0xFF) - 40
                    time.sleep(SLPTIME)

                    temps = mbdev.read_register(112, 0, 3, False)
                    most = (temps & 0xFF) - 40
                    balt = ((temps >> 8) & 0xFF) - 40
                    # balancer temperature is not handled separately in dbus-serialbattery,
                    # so let's display the max of both temperatures inside the BMS as mos temperature
                    self.temp_mos = max(most, balt)
                    time.sleep(SLPTIME)

                    return True

                except Exception as e:
                    logger.warn(
                        "Error reading SOC, retry ("
                        + str(n)
                        + "/"
                        + str(RETRYCNT)
                        + ") "
                        + str(e)
                    )
                    continue
                break
            logger.warn("Error reading SOC, failed")
        return False

    def read_cell_data(self):
        result = False
        mbdev = mbdevs[self.address]

        with locks[self.address]:
            for n in range(1, RETRYCNT):
                try:
                    cells = mbdev.read_registers(
                        81, number_of_registers=self.cell_count
                    )
                    time.sleep(SLPTIME)

                    balancing = mbdev.read_long(
                        139, 3, signed=False, byteorder=minimalmodbus.BYTEORDER_LITTLE
                    )
                    time.sleep(SLPTIME)

                    result = True
                except Exception as e:
                    logger.warn(
                        "read_cell_data() failed ("
                        + str(e)
                        + ") "
                        + str(n)
                        + "/"
                        + str(RETRYCNT)
                    )
                    continue
                break
            if result is False:
                return False

            if len(self.cells) != self.cell_count:
                self.cells = []
                for idx in range(self.cell_count):
                    self.cells.append(Cell(False))

            i = 0
            for cell in cells:
                cellV = ((cell & 0xFF) << 8) | ((cell >> 8) & 0xFF)
                self.cells[i].voltage = cellV / 1000
                self.cells[i].balance = balancing & (1 << i) != 0

                i = i + 1

        return True
