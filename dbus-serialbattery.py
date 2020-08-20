#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
from time import sleep
import serial
import gobject
import platform
import argparse
import logging
import sys
import os
from struct import *


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


degree_sign = u'\N{DEGREE SIGN}'
battery = Battery()
zero_char = chr(48)


def to_protection_bits(byte_data):
    tmp = bin(byte_data)[2:].rjust(13, zero_char)
    # voltage_high_cell
    # voltage_low_cell
    # voltage_high
    # voltage_low
    # temp_high_charge
    # temp_low_charge
    # temp_high_discharge
    # temp_low_discharge
    # current_over
    # current_under
    # short
    # IC_inspection
    # software_lock
    return False if tmp[12] == zero_char else True, False if tmp[11] == '0' else True, False if tmp[10] == '0' else True, \
        False if tmp[9] == '0' else True, False if tmp[8] == '0' else True, False if tmp[7] == '0' else True, \
        False if tmp[6] == '0' else True, False if tmp[5] == '0' else True, False if tmp[4] == '0' else True, \
        False if tmp[3] == '0' else True, False if tmp[2] == '0' else True, False if tmp[1] == '0' else True, \
        False if tmp[0] == '0' else True


def to_cell_bits(byte_data, length, cells):
    tmp = bin(byte_data)[2:].rjust(length, zero_char)
    for bit in reversed(tmp):
        c = Cell(False if bit == zero_char else True)
        cells.append(c)


def to_fet_bits(byte_data):
    tmp = bin(byte_data)[2:].rjust(2, zero_char)
    # tmp[1] = charge, tmp[0] = discharge
    return False if tmp[1] == zero_char else True, False if tmp[0] == zero_char else True


def log_battery_data(battery_data):
    voltage = str(battery_data.voltage / 100)
    current = str(battery_data.current / 100)
    remain = str(battery_data.capacity_remain / 100)
    cap = str(battery_data.capacity / 100)
    print ("voltage    {0}V   current  {1}A".format(voltage,current))
    print ("   capacity   {0}Ah of {1}Ah   SOC {2}%".format(remain,cap,battery_data.soc))

    for c in range(battery_data.cell_count):
        cell = str(c + 1)
        balance = "B" if battery_data.cells[c].balance else " "
        cell_volt = str(battery_data.cells[c].voltage / 1000)
        print ("C[" + cell.rjust(2, zero_char) + "]  " + balance + cell_volt + "V")


with serial.Serial('/dev/ttyUSB2', baudrate=9600, timeout=0.1) as ser:
    print(ser.name)

    def read_data_stream(command):
        ser.write(command)

        count = 0
        toread = ser.inWaiting()
        while toread < 4:
            sleep(0.01)
            toread = ser.inWaiting()
            count += 1
            if count > 40:
                print(">>> ERROR: No reply")
                exit(1)

        # toread = 4
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
            return data[4:]
        else:
            print(">>> ERROR: Incorrect Reply")
            return


    def read_gen_data(battery_data):
        command_general = b"\xDD\xA5\x03\x00\xFF\xFD\x77"
        # ser.write(command_general)

        gen_data = read_data_stream(command_general)

        battery_data.voltage, battery_data.current, battery_data.capacity_remain, battery_data.capacity, \
            battery_data.cycles, battery_data.production, balance, battery_data.balance2, protection, \
            version, battery_data.soc, fet, battery_data.cell_count, battery_data.temp_censors, \
            battery_data.temp1, battery_data.temp2 \
            = unpack_from('>HhHHHHhHHBBBBBHH', gen_data)

        to_cell_bits(balance, battery_data.cell_count, battery_data.cells)
        battery_data.version = float(str(version >> 4 & 0x0F) + "." + str(version & 0x0F))
        battery_data.charge_fet, battery_data.discharge_fet = to_fet_bits(fet)
        battery_data.protection.voltage_high_cell, battery_data.protection.voltage_low_cell, \
            battery_data.protection.voltage_high, battery_data.protection.voltage_low, \
            battery_data.protection.temp_high_charge, battery_data.protection.temp_low_charge, \
            battery_data.protection.temp_high_discharge, battery_data.protection.temp_low_discharge, \
            battery_data.protection.current_over, battery_data.protection.current_under, \
            battery_data.protection.short, battery_data.protection.IC_inspection, \
            battery_data.protection.software_lock \
            = to_protection_bits(protection)


    def read_cell_data(battery_data):
        command_cell = b"\xDD\xA5\x04\x00\xFF\xFC\x77"
        # ser.write(command_cell)

        cell_data = read_data_stream(command_cell)
        for c in range(battery_data.cell_count):
            battery_data.cells[c].voltage = unpack_from('>H', cell_data, c * 2)[0]


    for x in range(50):
        os.system('cls' if os.name == 'nt' else 'clear')
        read_gen_data(battery)
        read_cell_data(battery)
        log_battery_data(battery)
        sleep(7)
        print ("")


if __name__ == "__main__":
    main()