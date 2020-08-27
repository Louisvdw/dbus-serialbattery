#!/usr/bin/python -u
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
from time import sleep
from dbus.mainloop.glib import DBusGMainLoop
from struct import *
from threading import Thread
import serial
import dbus
import gobject
import traceback
import platform
import logging
import sys
import os

# Victron packages
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '/opt/victronenergy/dbus-systemcalc-py/ext/velib_python'))
from vedbus import VeDbusService

# Logging
logging.info('Starting dbus-serialbattery')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Protection:
    voltage_high_cell = False
    voltage_low_cell = False
    voltage_high = False
    voltage_low = False
    temp_high_charge = False
    temp_low_charge = False
    temp_high_discharge = False
    temp_low_discharge = False
    current_over = False
    current_under = False
    short = False
    IC_inspection = False
    software_lock = False


class Cell:
    voltage = 0
    balance = False

    def __init__(self, balance):
        self.balance = balance


def read_serial_data(command, port):
    with serial.Serial(port, baudrate=9600, timeout=0.1) as ser:
        ser.write(command)

        count = 0
        toread = ser.inWaiting()
        while toread < 4:
            sleep(0.01)
            toread = ser.inWaiting()
            count += 1
            if count > 50:
                logger.error(">>> ERROR: No reply")
                exit(1)

        res = ser.read(toread)
        start, flag, command1, length = unpack_from('BBBB', res)

        data = bytearray(res)
        while len(data) <= length + 6:
            res = ser.read(length+3)
            data.extend(res)
            sleep(0.2)

        checksum, end = unpack_from('HB', data, length+4)

        if end == 119:
            # logger.info("start=" + str(start))
            # logger.info("flag=" + str(flag))
            # logger.info("command=" + str(command1))
            # logger.info("data length=" + str(length))
            # logger.info("checksum=" + str(checksum))
            # logger.info("end=" + str(end))
            return data[4:length+4]
        else:
            logger.error(">>> ERROR: Incorrect Reply")
            return False


class Battery:
    hardware_version = ""
    voltage = 0
    current = 0
    capacity_remain = 0
    capacity = 0
    cycles = 0
    production = ""
    protection = Protection()
    version = 0
    soc = 0
    charge_fet = True
    discharge_fet = True
    cell_count = 0
    temp_censors = 0
    temp1 = 0
    temp2 = 0
    cells = []

    def __init__(self, port):
        self.port = port

    # degree_sign = u'\N{DEGREE SIGN}'
    command_general = b"\xDD\xA5\x03\x00\xFF\xFD\x77"
    command_cell = b"\xDD\xA5\x04\x00\xFF\xFC\x77"
    command_hardware = b"\xDD\xA5\x05\x00\xFF\xFB\x77"
    zero_char = chr(48)

    def to_protection_bits(self, byte_data):
        tmp = bin(byte_data)[2:].rjust(13, self.zero_char)
        self.protection.voltage_high_cell = self.is_bit_set(tmp[12])
        self.protection.voltage_low_cell = self.is_bit_set(tmp[11])
        self.protection.voltage_high = self.is_bit_set(tmp[10])
        self.protection.voltage_low = self.is_bit_set(tmp[9])
        self.protection.temp_high_charge = self.is_bit_set(tmp[8])
        self.protection.temp_low_charge = self.is_bit_set(tmp[7])
        self.protection.temp_high_discharge = self.is_bit_set(tmp[6])
        self.protection.temp_low_discharge = self.is_bit_set(tmp[5])
        self.protection.current_over = self.is_bit_set(tmp[4])
        self.protection.current_under = self.is_bit_set(tmp[3])
        self.protection.short = self.is_bit_set(tmp[2])
        self.protection.IC_inspection = self.is_bit_set(tmp[1])
        self.protection.software_lock = self.is_bit_set(tmp[0])

    def is_bit_set(self, tmp):
        return False if tmp == self.zero_char else True

    def to_cell_bits(self, byte_data):
        tmp = bin(byte_data)[2:].rjust(self.cell_count, self.zero_char)
        for c in self.cells:
            self.cells.remove(c)
        for bit in reversed(tmp):
            self.cells.append(Cell(self.is_bit_set(bit)))

    def to_fet_bits(self, byte_data):
        tmp = bin(byte_data)[2:].rjust(2, self.zero_char)
        self.charge_fet = self.is_bit_set(tmp[1])
        self.discharge_fet = self.is_bit_set(tmp[0])

    def log_battery_data(self):
        logger.debug("voltage    {0}V   current  {1}A".format(self.voltage, self.current))
        logger.debug("   capacity   {0}Ah of {1}Ah   SOC {2}%".format(self.capacity_remain, self.capacity, self.soc))

        for c in range(self.cell_count):
            cell = str(c + 1)
            balance = "B" if self.cells[c].balance else " "
            cell_volt = str(self.cells[c].voltage)
            logger.debug("C[" + cell.rjust(2, self.zero_char) + "]  " + balance + cell_volt + "V")

    def publish_battery_dbus(self):
        # Update SOC, DC and System items
        self._dbusservice['/System/NrOfCellsPerBattery'] = self.cell_count
        self._dbusservice['/Soc'] = round(self.soc, 2)
        self._dbusservice['/Dc/0/Voltage'] = round(self.voltage, 2)
        self._dbusservice['/Dc/0/Current'] = round(self.current, 2)
        self._dbusservice['/Dc/0/Power'] = round(self.voltage * self.current, 2)
        self._dbusservice['/Dc/0/Temperature'] = round((float(self.temp1) + float(self.temp2)) / 2, 2)

        # Update battery extras
        self._dbusservice['/History/ChargeCycles'] = self.cycles
        self._dbusservice['/Io/AllowToCharge'] = 1 if self.charge_fet else 0
        self._dbusservice['/Io/AllowToDischarge'] = 1 if self.discharge_fet else 0
        self._dbusservice['/System/MinCellTemperature'] = min(self.temp1, self.temp2)
        self._dbusservice['/System/MaxCellTemperature'] = max(self.temp1, self.temp2)

        # Updates from cells
        max_voltage = 0
        max_cell = ''
        min_voltage = 99
        min_cell = ''
        balance = False
        for c in range(self.cell_count):
            if max_voltage < self.cells[c].voltage:
                max_voltage = self.cells[c].voltage
                max_cell = c
            if min_voltage > self.cells[c].voltage:
                min_voltage = self.cells[c].voltage
                min_cell = c
            if self.cells[c].balance:
                balance = True
        self._dbusservice['/System/MaxCellVoltage'] = max_voltage
        self._dbusservice['/System/MaxVoltageCellId'] = 'C' + str(max_cell + 1)
        self._dbusservice['/System/MinCellVoltage'] = min_voltage
        self._dbusservice['/System/MinVoltageCellId'] = 'C' + str(min_cell + 1)
        self._dbusservice['/Balancing'] = 1 if balance else 0

        # Update the alarms
        self._dbusservice['/Alarms/LowVoltage'] = 2 if self.protection.voltage_low else 0
        self._dbusservice['/Alarms/HighVoltage'] = 2 if self.protection.voltage_high else 0
        self._dbusservice['/Alarms/LowSoc'] = 2 if self.soc < 10 else 1 if self.soc < 20 else 0
        self._dbusservice['/Alarms/HighChargeCurrent'] = 1 if self.protection.current_over else 0
        self._dbusservice['/Alarms/HighDischargeCurrent'] = 1 if self.protection.current_under else 0
        self._dbusservice['/Alarms/CellImbalance'] = 2 if self.protection.voltage_low_cell \
                                                          or self.protection.voltage_high_cell else 0
        self._dbusservice['/Alarms/InternalFailure'] = 2 if self.protection.short \
                                                            or self.protection.IC_inspection \
                                                            or self.protection.software_lock else 0
        self._dbusservice['/Alarms/HighChargeTemperature'] = 1 if self.protection.temp_high_charge else 0
        self._dbusservice['/Alarms/LowChargeTemperature'] = 1 if self.protection.temp_low_charge else 0
        self._dbusservice['/Alarms/HighTemperature'] = 1 if self.protection.temp_high_discharge else 0
        self._dbusservice['/Alarms/LowTemperature'] = 1 if self.protection.temp_low_discharge else 0

        logging.debug("logged to dbus ", round(self.voltage / 100, 2), round(self.current / 100, 2), round(self.soc, 2))

    def read_gen_data(self):
        gen_data = read_serial_data(self.command_general, self.port)
        # check if connect sucess
        if gen_data is False:
            return gen_data

        voltage, current, capacity_remain, capacity, self.cycles, self.production, balance, \
            balance2, protection, version, self.soc, fet, self.cell_count, self.temp_censors, temp1, temp2 \
            = unpack_from('>HhHHHHhHHBBBBBHH', gen_data)
        self.voltage = voltage / 100
        self.current = current / 100
        self.capacity_remain = capacity_remain / 100
        self.capacity = capacity / 100
        self.temp1 = (temp1 - 2731) / 10
        self.temp2 = (temp2 - 2731) / 10
        self.to_cell_bits(balance)
        self.version = float(str(version >> 4 & 0x0F) + "." + str(version & 0x0F))
        self.to_fet_bits(fet)
        self.to_protection_bits(protection)

    def read_cell_data(self):
        cell_data = read_serial_data(self.command_cell, self.port)
        # check if connect sucess
        if cell_data is False:
            return cell_data

        for c in range(self.cell_count):
            self.cells[c].voltage = unpack_from('>H', cell_data, c * 2)[0] / 1000

    def read_hardware_data(self):
        hardware_data = read_serial_data(self.command_hardware, self.port)
        # check if connect sucess
        if hardware_data is False:
            return hardware_data

        self.hardware_version = unpack_from('>' + str(len(hardware_data)) + 's', hardware_data)[0]
        logger.info(self.hardware_version)
        return True

    def publish_battery(self, loop):
        try:
            self.read_gen_data()
            self.read_cell_data()
            # self.log_battery_data()
            self.publish_battery_dbus()
        except:
            traceback.print_exc()
            loop.quit()

    def setup_vedbus(self, instance):

        self._dbusservice = VeDbusService("com.victronenergy.battery." + self.port[self.port.rfind('/')+1:])

        logger.debug("%s /DeviceInstance = %d" % ("com.victronenergy.battery." + self.port[self.port.rfind('/')+1:],
                                                   instance))

        # Create the management objects, as specified in the ccgx dbus-api document
        self._dbusservice.add_path('/Mgmt/ProcessName', __file__)
        self._dbusservice.add_path('/Mgmt/ProcessVersion', 'Python ' + platform.python_version())
        self._dbusservice.add_path('/Mgmt/Connection', 'Serial ' + self.port)

        # Create the mandatory objects
        self._dbusservice.add_path('/DeviceInstance', instance)
        self._dbusservice.add_path('/ProductId', 0x0)
        self._dbusservice.add_path('/ProductName', 'SerialBattery for LLT Smart BMS')
        self._dbusservice.add_path('/FirmwareVersion', self.version)
        self._dbusservice.add_path('/HardwareVersion', self.hardware_version)
        self._dbusservice.add_path('/Connected', 1)
        # Create static battery info
        self._dbusservice.add_path('/Info/BatteryLowVoltage', 46.0)
        self._dbusservice.add_path('/Info/MaxChargeVoltage', 52.5)
        self._dbusservice.add_path('/Info/MaxChargeCurrent', 50.0)
        self._dbusservice.add_path('/Info/MaxDischargeCurrent', 70.0)
        self._dbusservice.add_path('/System/NrOfCellsPerBattery', self.cell_count, writeable=True)
        self._dbusservice.add_path('/System/NrOfModulesOnline', 1, writeable=True)
        self._dbusservice.add_path('/System/NrOfModulesOffline', None, writeable=True)
        # Not used at this stage
        # self._dbusservice.add_path('/System/NrOfModulesBlockingCharge', None, writeable=True)
        # self._dbusservice.add_path('/System/NrOfModulesBlockingDischarge', None, writeable=True)
        # self._dbusservice.add_path('/System/MinTemperatureCellId', None, writeable=True)
        # self._dbusservice.add_path('/System/MaxTemperatureCellId', None, writeable=True)
        self._dbusservice.add_path('/Capacity', self.capacity, writeable=True)
        # Create SOC, DC and System items
        self._dbusservice.add_path('/Soc', None, writeable=True)
        self._dbusservice.add_path('/Dc/0/Voltage', None, writeable=True)
        self._dbusservice.add_path('/Dc/0/Current', None, writeable=True)
        self._dbusservice.add_path('/Dc/0/Power', None, writeable=True)
        self._dbusservice.add_path('/Dc/0/Temperature', 21.0, writeable=True)
        # Create battery extras
        self._dbusservice.add_path('/System/MinCellTemperature', None, writeable=True)
        self._dbusservice.add_path('/System/MaxCellTemperature', None, writeable=True)
        self._dbusservice.add_path('/System/MaxCellVoltage', 0.0, writeable=True)
        self._dbusservice.add_path('/System/MaxVoltageCellId', '', writeable=True)
        self._dbusservice.add_path('/System/MinCellVoltage', 0.0, writeable=True)
        self._dbusservice.add_path('/System/MinVoltageCellId', '', writeable=True)
        self._dbusservice.add_path('/History/ChargeCycles', 0, writeable=True)
        self._dbusservice.add_path('/Balancing', 0, writeable=True)
        self._dbusservice.add_path('/Io/AllowToCharge', 0, writeable=True)
        self._dbusservice.add_path('/Io/AllowToDischarge', 0, writeable=True)
        # Create the alarms
        self._dbusservice.add_path('/Alarms/LowVoltage', 0, writeable=True)
        self._dbusservice.add_path('/Alarms/HighVoltage', 0, writeable=True)
        self._dbusservice.add_path('/Alarms/LowSoc', 0, writeable=True)
        self._dbusservice.add_path('/Alarms/HighChargeCurrent', 0, writeable=True)
        self._dbusservice.add_path('/Alarms/HighDischargeCurrent', 0, writeable=True)
        self._dbusservice.add_path('/Alarms/CellImbalance', 0, writeable=True)
        self._dbusservice.add_path('/Alarms/InternalFailure', 0, writeable=True)
        self._dbusservice.add_path('/Alarms/HighChargeTemperature', 0, writeable=True)
        self._dbusservice.add_path('/Alarms/LowChargeTemperature', 0, writeable=True)
        self._dbusservice.add_path('/Alarms/HighTemperature', 0, writeable=True)
        self._dbusservice.add_path('/Alarms/LowTemperature', 0, writeable=True)


INTERVAL = 3000


def main():

    def poll_battery(loop):
        # Run in separate thread. Pass in the mainloop so the thread can kill us if there is an exception.
        poller = Thread(target=lambda: battery.publish_battery(loop))
        # Tread will die with us if deamon
        poller.daemon = True
        poller.start()
        return True

    logger.info('dbus-serialbattery')
    # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
    DBusGMainLoop(set_as_default=True)
    # create a new battery object that can read the battery
    port = '/dev/ttyUSB2'
    battery = Battery(port)
    result = battery.read_hardware_data()
    if result is False:
        logger.error("ERROR >>> No battery connection at " + port)
        return

    gobject.threads_init()
    mainloop = gobject.MainLoop()
    # Get the initial values for the battery used by setup_vedbus
    battery.read_gen_data()
    battery.setup_vedbus(instance=1)
    logger.info('Battery connected to dbus from ' + port)

    # Poll the battery at INTERVAL and run the main loop
    gobject.timeout_add(INTERVAL, lambda: poll_battery(mainloop))
    try:
        mainloop.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
