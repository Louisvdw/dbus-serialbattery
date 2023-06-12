# -*- coding: utf-8 -*-
from battery import Battery, Cell
from utils import logger
import utils
import serial
from time import sleep


class HLPdataBMS4S(Battery):
    def __init__(self, port, baud, address):
        super(HLPdataBMS4S, self).__init__(port, baud, address)
        self.type = self.BATTERYTYPE

    BATTERYTYPE = "HLPdataBMS4S"

    def test_connection(self):
        # call a function that will connect to the battery, send a command and retrieve the result.
        # The result or call should be unique to this BMS. Battery name or version, etc.
        # Return True if success, False for failure
        result = False
        try:
            result = self.read_test_data()
        except Exception as err:
            logger.error(f"Unexpected {err=}, {type(err)=}")
            result = False

        # give the user a feedback that no BMS was found
        if not result:
            logger.error(">>> ERROR: No reply - returning")

        return result

    def get_settings(self):
        # After successful  connection get_settings will be call to set up the battery.
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

        # def log_settings(self):
        #    logger.info(f'Battery {self.type} connected to dbus from {self.port}')
        #    logger.info(f'=== Settings ===')
        #    cell_counter = len(self.cells)
        #    logger.info(f'> Connection voltage {self.voltage}V | current {self.current}A | SOC {self.soc}%')
        #    logger.info(f'> Cell count {self.cell_count} | cells populated {cell_counter}')
        #    logger.info(f'> CCCM SOC {CCCM_SOC_ENABLE} | DCCM SOC {DCCM_SOC_ENABLE}')
        #    logger.info(f'> CCCM CV {CCCM_CV_ENABLE} | DCCM CV {DCCM_CV_ENABLE}')
        #    logger.info(f'> CCCM T {CCCM_T_ENABLE} | DCCM T {DCCM_T_ENABLE}')
        #    logger.info(f'> MIN_CELL_VOLTAGE {MIN_CELL_VOLTAGE}V | MAX_CELL_VOLTAGE {MAX_CELL_VOLTAGE}V')

        return

    def read_test_data(self):
        test_data = self.read_serial_data_HLPdataBMS4S(b"pv\n", 1, 15)
        if test_data is False:
            return False
        s1 = str(test_data)
        ix = s1.find("BMS4S")
        if ix > 0:
            self.hardware_version = s1[ix : len(s1) - 1]
            self.version = self.hardware_version
            self.max_battery_charge_current = utils.MAX_BATTERY_CHARGE_CURRENT
            self.max_battery_discharge_current = utils.MAX_BATTERY_DISCHARGE_CURRENT
            self.poll_interval = 10000
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
            return True
        return False

    def read_settings_data(self):
        test_data = self.read_serial_data_HLPdataBMS4S(b"ps\n", 3, 700)
        if test_data is False:
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
        self.max_battery_voltage = float(v) * float(4)
        v = get_par("VoltLow= ", s)
        if v is False:
            return False
        self.min_battery_voltage = float(v) * float(4)

        return True

    def read_status_data(self):
        status_data = self.read_serial_data_HLPdataBMS4S(b"m1\n", 0.2, 40)
        if status_data is False:
            return False
        par1 = str(status_data)
        par = par1.split(",")
        if len(par) < 8:
            return False
        if len(par[0]) < 7:
            return False
        p0 = str(par[0])
        ix = p0.find(".")
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
        self.control_allow_charge = par[6]
        self.charge_fet = par[6]
        self.control_allow_discharge = par[7]
        self.discharge_fet = par[7]

        beep = int(par[11])
        if beep == 2:
            self.protection.temp_low_charge = 1
        else:
            self.protection.temp_low_charge = 0
        if beep == 3:
            self.protection.temp_high_charge = 1
        else:
            self.protection.temp_high_charge = 0
        if beep == 4:
            self.protection.voltage_low = 2
        else:
            self.protection.voltage_low = 0
        if beep == 5:
            self.protection.voltage_high = 2
        else:
            self.protection.voltage_high = 0

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
                    temp = int("".join(filter(str.isdigit, tmp[1])))
                    if name[0] == "b":
                        nb += 1
                        if temp > max:
                            max = temp
                        if temp < min:
                            min = temp
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
        if data is False:
            return False
        return data


def read_serial_data(command, port, baud, time, min_len):
    try:
        with serial.Serial(port, baudrate=baud, timeout=0.5) as ser:
            ret = read_serialport_data(ser, command, time, min_len)
            if ret is True:
                return ret
        return False

    except serial.SerialException as e:
        logger.error(e)
        return False

    except Exception:
        return False


def read_serialport_data(ser, command, time, min_len):
    try:
        cnt = 0
        while cnt < 3:
            cnt += 1
            ser.flushOutput()
            ser.flushInput()
            ser.write(command)
            sleep(time)
            res = ser.read(1000)
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
