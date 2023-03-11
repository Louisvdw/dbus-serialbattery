# -*- coding: utf-8 -*-
from battery import Protection, Battery, Cell
from utils import *
from struct import *
import locale
import serial
from time import sleep


class HLPdataBMS4S(Battery):
    def __init__(self, port, baud):
        super(HLPdataBMS4S, self).__init__(port, baud)
        self.type = self.BATTERYTYPE

    BATTERYTYPE = "HLPdataBMS4S"

    def test_connection(self):
        # call a function that will connect to the battery, send a command and retrieve the result.
        # The result or call should be unique to this BMS. Battery name or version, etc.
        # Return True if success, False for failure
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        result = False
        try:
            result = self.read_test_data()
        except Exception as e:
            logger.info(e, exc_info=True)
            pass

        return result

    def get_settings(self):
        # After successful  connection get_settings will be call to set up the battery.
        # Set the current limits, populate cell count, etc
        # Return True if success, False for failure
        result = False
        try:
            result = self.read_settings_data()
        except Exception as e:
#            logger.info(e, exc_info=True)
            pass
        return result

    def refresh_data(self):
        # call all functions that will refresh the battery data.
        # This will be called for every iteration (1 second)
        # Return True if success, False for failure
        result = False
        try:
            result = self.read_status_data()
        except Exception as e:
#            logger.info(e, exc_info=True)
            pass

        return result

    def read_test_data(self):
        test_data = self.read_serial_data_HLPdataBMS4S(b"pv\n", 0.08)
        if test_data is False:
            return False
        if len(test_data) >= 15:
            s1 = str(test_data)
            ix = s1.find("BMS4S")
            if ix > 0:
                self.hardware_version = s1[ix:len(s1)-1]
                self.version = self.hardware_version
                return True
        return False

    def read_settings_data(self):
        self.max_battery_charge_current = MAX_BATTERY_CHARGE_CURRENT
        self.max_battery_discharge_current = MAX_BATTERY_DISCHARGE_CURRENT
        self.poll_interval = 5000
        self.control_discharge_current = 1000
        self.control_charge_current = 1000
        self.soc = 50
        self.voltage = 13.2
        self.current = 0
        self.min_battery_voltage = 12.0
        self.max_battery_voltage = 14.4

        if self.cell_count is None:
            self.cell_count = 4
            for c in range(self.cell_count):
                self.cells.append(Cell(False))
        test_data = self.read_serial_data_HLPdataBMS4S(b"ps\n", 1.0)
        if test_data is False:
            return False
        if len(test_data) < 500:
            return False
        s = str(test_data)
        s = s.replace(",", ".")
        par = get_par("BatterySize= ", s)
        if par is False:
            return False
        self.capacity = int(par)
        v = get_par("VoltHigh= ", s)
        if v is False:
            return False
        self.max_battery_voltage = float(v)*float(4)
        v = get_par("VoltLow= ", s)
        if v is False:
            return False
        self.min_battery_voltage = float(v)*float(4)

        return True


    def read_status_data(self):
        status_data = self.read_serial_data_HLPdataBMS4S(b"m1\n", 0.1)
        if status_data is False:
            return False
        par1 = str(status_data)
        par = par1.split(",")
        if len(par) < 8:
            return False
        if len(par[0]) < 7:
            return False
        p0 = str(par[0])
        ix = p0.find('.')
        par0 = p0[ix-1:len(p0)]

# v1,v2,v3,v4,current,soc,chargeoff,loadoff,vbat2,socnow,adj,beep,led,temp1,temp2...
# 0  1  2  3  4       5   6         7       8     9      10  11   12  13    14...

        self.voltage = float(par0) + float(par[1]) + float(par[2]) + float(par[3])
        self.cells[0].voltage = float(par0)
#        self.cells[0].temp = 20
        self.cells[1].voltage = float(par[1])
#        self.cells[0].temp = 20
        self.cells[2].voltage = float(par[2])
#        self.cells[0].temp = 20
        self.cells[3].voltage = float(par[3])
#        self.cells[0].temp = 20

        self.current = float(par[4])
        self.soc = int(par[5])

        if par[6] == "0":
            self.control_allow_charge = False
        else:
            self.control_allow_charge = True
        if par[7] == "0":
            self.control_allow_discharge = False
        else:
            self.control_allow_discharge = True
        return True

    def manage_charge_voltage(self):
        self.allow_max_voltage = True
        self.control_voltage = self.max_battery_voltage

    def manage_charge_current(self):
        self.control_charge_current = 1000
        self.control_discharge_current = 1000

    def read_serial_data_HLPdataBMS4S(self, command, time):
        data = read_serial_data2(command, self.port, self.baud_rate, time)
        if data is False:
            return False
        return data



def read_serial_data2(command, port, baud, time):
    try:
        with serial.Serial(port, baudrate=baud, timeout=0.1) as ser:
            return read_serialport_data2(ser, command, time)

    except serial.SerialException as e:
        logger.error(e)
        return False

def read_serialport_data2(ser, command, time):
    try:
        ser.flushOutput()
        ser.flushInput()
        ser.write(command)

        sleep(time)
        res = ser.read(1000)
        if len(res) > 0:
            return res
        return False

    except serial.SerialException as e:
        logger.error(e)
        return False

def get_par(p, s):
    ix = s.find(p)
    if ix > 0:
        ix += len(p)
        for i in range(ix, len(s)):
            if s[i] == ' ' or s[i] == 10:
                ret = s[ix:i]
                return ret
    return False
