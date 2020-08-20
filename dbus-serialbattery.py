#!/usr/bin/python -u
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
from time import sleep
from vedbus import VeDbusService
from settingsdevice import SettingsDevice
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
from logger import setup_logging

sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'ext', 'velib_python'))

logger = setup_logging(debug=True)


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


def read_serial_data(command):
    with serial.Serial('/dev/ttyUSB2', baudrate=9600, timeout=0.1) as ser:
        ser.write(command)

        count = 0
        toread = ser.inWaiting()
        while toread < 4:
            sleep(0.01)
            toread = ser.inWaiting()
            count += 1
            if count > 50:
                print(">>> ERROR: No reply")
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
            # print("start=" + str(start))
            # print("flag=" + str(flag))
            # print("command=" + str(command1))
            # print("data length=" + str(length))
            # print("checksum=" + str(checksum))
            # print("end=" + str(end))
            return data[4:length]
        else:
            print(">>> ERROR: Incorrect Reply")
            return


class Battery:
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

    # degree_sign = u'\N{DEGREE SIGN}'
    command_cell = b"\xDD\xA5\x04\x00\xFF\xFC\x77"
    command_general = b"\xDD\xA5\x03\x00\xFF\xFD\x77"
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
        for bit in reversed(tmp):
            self.cells.append(Cell(self.is_bit_set(bit)))

    def to_fet_bits(self, byte_data):
        tmp = bin(byte_data)[2:].rjust(2, self.zero_char)
        self.charge_fet = self.is_bit_set(tmp[1])
        self.discharge_fet = self.is_bit_set(tmp[0])

    def log_battery_data(self):
        voltage = str(self.voltage / 100)
        current = str(self.current / 100)
        remain = str(self.capacity_remain / 100)
        cap = str(self.capacity / 100)
        print("voltage    {0}V   current  {1}A".format(voltage, current))
        print("   capacity   {0}Ah of {1}Ah   SOC {2}%".format(remain, cap, self.soc))

        for c in range(self.cell_count):
            cell = str(c + 1)
            balance = "B" if self.cells[c].balance else " "
            cell_volt = str(self.cells[c].voltage / 1000)
            print("C[" + cell.rjust(2, self.zero_char) + "]  " + balance + cell_volt + "V")

    def read_gen_data(self, battery_data):
        gen_data = read_serial_data(self.command_general)

        self.voltage, self.current, self.capacity_remain, self.capacity, self.cycles, self.production, balance, \
            balance2, protection, version, self.soc, fet, self.cell_count, self.temp_censors, self.temp1, self.temp2 \
            = unpack_from('>HhHHHHhHHBBBBBHH', gen_data)
        self.to_cell_bits(balance)
        self.version = float(str(version >> 4 & 0x0F) + "." + str(version & 0x0F))
        self.to_fet_bits(fet)
        self.to_protection_bits(protection)

    def read_cell_data(self):
        cell_data = read_serial_data(self.command_cell)
        for c in range(self.cell_count):
            self.cells[c].voltage = unpack_from('>H', cell_data, c * 2)[0]

    def publish_battery(self):
        self.read_gen_data()
        self.read_cell_data()
        self.log_battery_data()


class SystemBus(dbus.bus.BusConnection):
    def __new__(cls):
        return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SYSTEM)


class SessionBus(dbus.bus.BusConnection):
    def __new__(cls):
        return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SESSION)


def dbusconnection():
    return SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else SystemBus()


INTERVAL = 6000


def main():
    # create a new battery object that can read the batter
    # battery = Battery()

    # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
    # DBusGMainLoop(set_as_default=True)

    def poll_battery(loop, bat):
        from time import time
        idx = 0

        try:
            # bat.publish_battery()
            logging.info('publishing battery {0}V', bat.voltage)
        except:
            traceback.print_exc()
            loop.quit()

    # Run in separate thread. Pass in the mainloop so the thread can kill us if there is an exception.
    gobject.threads_init()
    mainloop = gobject.MainLoop()

    poller = Thread(target=lambda: poll_battery(mainloop, battery))
    poller.daemon = True
    poller.start()

    gobject.timeout_add(INTERVAL, poller.run())

    try:
        mainloop.run()
    except KeyboardInterrupt:
        pass
    finally:
        pass


if __name__ == "__main__":
    main()
