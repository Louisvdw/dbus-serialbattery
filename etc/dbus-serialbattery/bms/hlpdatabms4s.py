# -*- coding: utf-8 -*-
from battery import Battery, Cell
from utils import logger
import serial
from time import sleep
import sys


class HLPdataBMS4S(Battery):
    def __init__(self, port, baud, address):
        super(HLPdataBMS4S, self).__init__(port, baud, address)
        self.type = self.BATTERYTYPE

    BATTERYTYPE = "HLPdataBMS4S"

    def test_connection(self):
        """
        call a function that will connect to the battery, send a command and retrieve the result.
        The result or call should be unique to this BMS. Battery name or version, etc.
        Return True if success, False for failure
        """
        result = False
        try:
            # get settings to check if the data is valid and the connection is working
            result = self.read_test_data()
            # get the rest of the data to be sure, that all data is valid and the correct battery type is recognized
            # only read next data if the first one was successful, this saves time when checking multiple battery types
            if result == True:
                result = self.get_settings()
            if result == True:
                result = self.refresh_data()
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

        # give the user a feedback that no BMS was found
        if not result:
            logger.error(">>> ERROR: No reply - returning")

        return result

    def get_settings(self):
        # After successful connection get_settings() will be called to set up the battery
        # Set the current limits, populate cell count, etc
        # Return True if success, False for failure
        result = False
        try:
            result = self.read_settings_data()
        except Exception as e:
            logger.error(e, exc_info=True)
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
            logger.error(e, exc_info=True)
            pass
        return result

    def unique_identifier(self) -> str:
        return "BMS4S_" + str(int(self.capacity))

    def read_test_data(self):
        test_data = self.read_serial_data_HLPdataBMS4S(b"pv\n", 0.3, 12)
        if test_data is False:
            return False
        s1 = str(test_data)
        ix = s1.find("BMS4S")
        if ix > 0:
            self.hardware_version = s1[ix : len(s1) - 1]
            self.version = self.hardware_version
            self.poll_interval = 10000
            self.control_discharge_current = 1000
            self.control_charge_current = 1000
            if self.cell_count is None:
                self.cell_count = 4
                for c in range(self.cell_count):
                    self.cells.append(Cell(False))
            return True
        return False

    def read_settings_data(self):
        test_data = self.read_serial_data_HLPdataBMS4S(b"ps\n", 2.0, 700)
        if test_data is False:
            return False
        s = str(test_data)
        s = s.replace(",", ".")
        par = get_par("BatterySize= ", s)
        if par is False:
            logger.error(">>> ERROR: BatterySize")
            return False
        self.capacity = int(par)
        v = get_par("VoltHigh= ", s)
        if v is False:
            logger.error(">>> ERROR: VoltHigh")
            return False
        self.max_battery_voltage = float(v) * float(4)
        v = get_par("VoltLow= ", s)
        if v is False:
            logger.error(">>> ERROR: VoltLow")
            return False
        self.min_battery_voltage = float(v) * float(4)
        return True

    def read_status_data(self):
        if self.cell_count is None:
            return False
        status_data = self.read_serial_data_HLPdataBMS4S(b"m1\n", 0.3, 40)
        if status_data is False:
            return False
        par2 = str(status_data)
        ix = par2.find("m1")
        if ix == -1:
            logger.error(">>> ERROR: m1 " + par1)
            return False
        par1 = par2[ix : len(par2)]
        par = par1.split(",")
        if len(par) < 13:
            logger.error(">>> ERROR: <13 " + par1)
            return False
        if len(par[0]) < 7:
            logger.error(">>> ERROR: <7 " + par1)
            return False
        p0 = str(par[0])
        ix = p0.find(".")
        if ix == -1:
            logger.error(">>> ERROR: ix " + par1)
            return False
        if str(par[3]).find(".") == -1:
            logger.error(">>> ERROR: par[3] " + par1)
            return False
        if str(par[11]).isdigit() is False:
            logger.error(">>> ERROR: par[11] " + par1)
            return False
        par0 = p0[ix - 1 : len(p0)]

        # v1,v2,v3,v4,current,soc,chargeoff,loadoff,vbat2,socnow,adj,beep,led,temp1,temp2...
        # 0  1  2  3  4       5   6         7       8     9      10  11   12  13    14...

        self.voltage = float(par0) + float(par[1]) + float(par[2]) + float(par[3])
        self.cells[0].voltage = float(par0)
        self.cells[1].voltage = float(par[1])
        self.cells[2].voltage = float(par[2])
        self.cells[3].voltage = float(par[3])
        self.current = float(par[4])
        self.soc = int(par[5])
        st = int(par[6]) == 1
        self.control_allow_charge = st
        self.charge_fet = st
        st = int(par[7]) == 1
        self.control_allow_discharge = st
        self.discharge_fet = st

        beep = int(par[11])
        if beep == 2:
            self.protection.low_charge_temp = 1
        else:
            self.protection.low_charge_temp = 0
        if beep == 3:
            self.protection.high_charge_temp = 1
        else:
            self.protection.high_charge_temp = 0
        if beep == 4:
            self.protection.low_voltage = 2
        else:
            self.protection.low_voltage = 0
        if beep == 5:
            self.protection.high_voltage = 2
        else:
            self.protection.high_voltage = 0
        if len(par) > 13:
            nb = 0
            min = int(1000)
            max = int(-1000)
            ix = 13
            while ix < len(par):
                tmp = par[ix].split(" ")
                ix += 1
                if len(tmp) == 2:
                    name = tmp[0]
                    if name[0] == "b":
                        temp = int("".join(filter(str.isdigit, tmp[1])))
                        nb += 1
                        if temp > max:
                            max = temp
                        if temp < min:
                            min = temp
                else:
                    logger.error(">>> ERROR: temp")
            if nb == 1:
                self.temp1 = max
            if nb > 1:
                self.temp1 = max
                self.temp2 = min
        return True

    def manage_charge_voltage(self):
        self.allow_max_voltage = True
        self.control_voltage = self.max_battery_voltage

    def manage_charge_current(self):
        self.control_charge_current = 1000
        self.control_discharge_current = 1000

    def read_serial_data_HLPdataBMS4S(self, command, time, min_len):
        data = read_serial_data(command, self.port, self.baud_rate, time, min_len)
        return data


def read_serial_data(command, port, baud, time, min_len):
    try:
        with serial.Serial(port, baudrate=baud, timeout=2.5) as ser:
            ret = read_serialport_data(ser, command, time, min_len)
        return ret

    except serial.SerialException as e:
        logger.error(e)
        return False

    except Exception:
        return False


def read_serialport_data(ser, command, time, min_len):
    try:
        if min_len == 12:
            ser.write(b"\n")
            sleep(0.2)
        cnt = 0
        while cnt < 3:
            cnt += 1
            ser.flushOutput()
            ser.flushInput()
            ser.write(command)
            sleep(time)
            toread = ser.inWaiting()
            res = ser.read(toread)
            if len(res) >= min_len:
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
            if s[i] == " " or s[i] == 10 or s[i] == 13:
                ret = s[ix:i]
                return ret
    return False
