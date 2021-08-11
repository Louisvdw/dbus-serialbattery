# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import sys
import os
import platform
import dbus
import traceback
# Victron packages
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '/opt/victronenergy/dbus-systemcalc-py/ext/velib_python'))
from vedbus import VeDbusService

from settingsdevice import SettingsDevice
import battery
from utils import *

def get_bus():
    return dbus.SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus()

class DbusHelper:

    def __init__(self, battery):
        self.battery = battery
        self.instance = 1
        self.settings = None
        self._dbusservice = VeDbusService("com.victronenergy.battery." +
                                          self.battery.port[self.battery.port.rfind('/') + 1:],
                                          get_bus())

    def setup_instance(self):
        path = '/Settings/Devices/serialbattery'
        default_instance = 'battery:1'
        settings = {'instance': [path + '/ClassAndVrmInstance', default_instance, 0, 0], }

        self.settings = SettingsDevice(get_bus(), settings, self.handle_changed_setting)
        self.battery.role, self.battery.instance = self.get_role_instance()

    def get_role_instance(self):
        val = self.settings['instance'].split(':')
        return val[0], int(val[1])

    def handle_changed_setting(self, setting, oldvalue, newvalue):
        if setting == 'instance':
            self.battery.role, self.instance = self.get_role_instance()
            self._dbusservice['/DeviceInstance'] = self.instance
            logger.debug("DeviceInstance = %d", self.instance)
            return

    def setup_vedbus(self):
        # Set up dbus service and device instance
        # and notify of all the attributes we intend to update
        self.setup_instance()
        logger.debug("%s" % ("com.victronenergy.battery." + self.battery.port[self.battery.port.rfind('/') + 1:]))

        # Get the settings for the battery
        if not self.battery.get_settings():
            return False

        # Create the management objects, as specified in the ccgx dbus-api document
        self._dbusservice.add_path('/Mgmt/ProcessName', __file__)
        self._dbusservice.add_path('/Mgmt/ProcessVersion', 'Python ' + platform.python_version())
        self._dbusservice.add_path('/Mgmt/Connection', 'Serial ' + self.battery.port)

        # Create the mandatory objects
        self._dbusservice.add_path('/DeviceInstance', self.instance)
        self._dbusservice.add_path('/ProductId', 0x0)
        self._dbusservice.add_path('/ProductName', 'SerialBattery (' + self.battery.type + ') v' +
                                   str(DRIVER_VERSION) + DRIVER_SUBVERSION)
        self._dbusservice.add_path('/FirmwareVersion', self.battery.version)
        self._dbusservice.add_path('/HardwareVersion', self.battery.hardware_version)
        self._dbusservice.add_path('/Connected', 1)
        # Create static battery info
        self._dbusservice.add_path('/Info/BatteryLowVoltage', self.battery.min_battery_voltage, writeable=True)
        self._dbusservice.add_path('/Info/MaxChargeVoltage', self.battery.max_battery_voltage, writeable=True,
                                   gettextcallback=lambda p, v: "{:0.2f}V".format(v))
        self._dbusservice.add_path('/Info/MaxChargeCurrent', self.battery.max_battery_current, writeable=True,
                                   gettextcallback=lambda p, v: "{:0.2f}A".format(v))
        self._dbusservice.add_path('/Info/MaxDischargeCurrent', self.battery.max_battery_discharge_current,
                                   writeable=True, gettextcallback=lambda p, v: "{:0.2f}A".format(v))
        self._dbusservice.add_path('/System/NrOfCellsPerBattery', self.battery.cell_count, writeable=True)
        self._dbusservice.add_path('/System/NrOfModulesOnline', 1, writeable=True)
        self._dbusservice.add_path('/System/NrOfModulesOffline', None, writeable=True)
        self._dbusservice.add_path('/System/NrOfModulesBlockingCharge', None, writeable=True)
        self._dbusservice.add_path('/System/NrOfModulesBlockingDischarge', None, writeable=True)
        self._dbusservice.add_path('/Capacity', self.battery.capacity_remain, writeable=True,
                                   gettextcallback=lambda p, v: "{:0.2f}Ah".format(v))
        self._dbusservice.add_path('/InstalledCapacity', self.battery.capacity, writeable=True,
                                   gettextcallback=lambda p, v: "{:0.0f}Ah".format(v))
        # Not used at this stage
        # self._dbusservice.add_path('/System/MinTemperatureCellId', None, writeable=True)
        # self._dbusservice.add_path('/System/MaxTemperatureCellId', None, writeable=True)
        # Create SOC, DC and System items
        self._dbusservice.add_path('/Soc', None, writeable=True)
        self._dbusservice.add_path('/Dc/0/Voltage', None, writeable=True, gettextcallback=lambda p, v: "{:0.2f}V".format(v))
        self._dbusservice.add_path('/Dc/0/Current', None, writeable=True, gettextcallback=lambda p, v: "{:0.2f}A".format(v))
        self._dbusservice.add_path('/Dc/0/Power', None, writeable=True, gettextcallback=lambda p, v: "{:0.0f}W".format(v))
        self._dbusservice.add_path('/Dc/0/Temperature', None, writeable=True)
        # Create battery extras
        self._dbusservice.add_path('/System/MinCellTemperature', None, writeable=True)
        self._dbusservice.add_path('/System/MaxCellTemperature', None, writeable=True)
        self._dbusservice.add_path('/System/MaxCellVoltage', None, writeable=True,
                                   gettextcallback=lambda p, v: "{:0.3f}V".format(v))
        self._dbusservice.add_path('/System/MaxVoltageCellId', None, writeable=True)
        self._dbusservice.add_path('/System/MinCellVoltage', None, writeable=True,
                                   gettextcallback=lambda p, v: "{:0.3f}V".format(v))
        self._dbusservice.add_path('/System/MinVoltageCellId', None, writeable=True)
        self._dbusservice.add_path('/History/ChargeCycles', None, writeable=True)
        self._dbusservice.add_path('/Balancing', None, writeable=True)
        self._dbusservice.add_path('/Io/AllowToCharge', 0, writeable=True)
        self._dbusservice.add_path('/Io/AllowToDischarge', 0, writeable=True)
        # Create the alarms
        self._dbusservice.add_path('/Alarms/LowVoltage', None, writeable=True)
        self._dbusservice.add_path('/Alarms/HighVoltage', None, writeable=True)
        self._dbusservice.add_path('/Alarms/LowSoc', None, writeable=True)
        self._dbusservice.add_path('/Alarms/HighChargeCurrent', None, writeable=True)
        self._dbusservice.add_path('/Alarms/HighDischargeCurrent', None, writeable=True)
        self._dbusservice.add_path('/Alarms/CellImbalance', None, writeable=True)
        self._dbusservice.add_path('/Alarms/InternalFailure', None, writeable=True)
        self._dbusservice.add_path('/Alarms/HighChargeTemperature', None, writeable=True)
        self._dbusservice.add_path('/Alarms/LowChargeTemperature', None, writeable=True)
        self._dbusservice.add_path('/Alarms/HighTemperature', None, writeable=True)
        self._dbusservice.add_path('/Alarms/LowTemperature', None, writeable=True)

        return True

    def publish_battery(self, loop):
        try:
            self.battery.refresh_data()
            self.battery.manage_charge_current()
            # self.battery.manage_control_charging(max_voltage, min_voltage, total_voltage, balance)
            self.publish_dbus()
        except:
            traceback.print_exc()
            loop.quit()

    def publish_dbus(self):
        # Update SOC, DC and System items
        self._dbusservice['/System/NrOfCellsPerBattery'] = self.battery.cell_count
        self._dbusservice['/Soc'] = round(self.battery.soc, 2)
        self._dbusservice['/Dc/0/Voltage'] = round(self.battery.voltage, 2)
        self._dbusservice['/Dc/0/Current'] = round(self.battery.current, 2)
        self._dbusservice['/Dc/0/Power'] = round(self.battery.voltage * self.battery.current, 2)
        self._dbusservice['/Dc/0/Temperature'] = self.battery.get_temp()
        self._dbusservice['/Capacity'] = self.battery.capacity_remain

        # Update battery extras
        self._dbusservice['/History/ChargeCycles'] = self.battery.cycles
        self._dbusservice['/Io/AllowToCharge'] = 1 if self.battery.charge_fet \
                                                      and self.battery.control_allow_charge else 0
        self._dbusservice['/Io/AllowToDischarge'] = 1 if self.battery.discharge_fet else 0
        self._dbusservice['/System/NrOfModulesBlockingCharge'] = 0 if self.battery.charge_fet \
                                                        and self.battery.control_allow_charge else 1
        self._dbusservice['/System/MinCellTemperature'] = self.battery.get_min_temp()
        self._dbusservice['/System/MaxCellTemperature'] = self.battery.get_max_temp()

        # Charge control
        self._dbusservice['/Info/MaxChargeCurrent'] = self.battery.control_charge_current
        self._dbusservice['/Info/MaxDischargeCurrent'] = self.battery.control_discharge_current

        # Updates from cells
        self._dbusservice['/System/MinVoltageCellId'] = self.battery.get_min_cell_desc()
        self._dbusservice['/System/MaxVoltageCellId'] = self.battery.get_max_cell_desc()
        self._dbusservice['/System/MinCellVoltage'] = self.battery.get_min_cell_voltage()
        self._dbusservice['/System/MaxCellVoltage'] = self.battery.get_max_cell_voltage()
        self._dbusservice['/Balancing'] = self.battery.get_balancing()

        # Update the alarms
        self._dbusservice['/Alarms/LowVoltage'] = self.battery.protection.voltage_low
        self._dbusservice['/Alarms/HighVoltage'] = self.battery.protection.voltage_high
        self._dbusservice['/Alarms/LowSoc'] = self.battery.protection.soc_low
        self._dbusservice['/Alarms/HighChargeCurrent'] = self.battery.protection.current_over
        self._dbusservice['/Alarms/HighDischargeCurrent'] = self.battery.protection.current_under
        self._dbusservice['/Alarms/CellImbalance'] = self.battery.protection.cell_imbalance
        self._dbusservice['/Alarms/InternalFailure'] = self.battery.protection.internal_failure
        self._dbusservice['/Alarms/HighChargeTemperature'] = self.battery.protection.temp_high_charge
        self._dbusservice['/Alarms/LowChargeTemperature'] = self.battery.protection.temp_low_charge
        self._dbusservice['/Alarms/HighTemperature'] = self.battery.protection.temp_high_discharge
        self._dbusservice['/Alarms/LowTemperature'] = self.battery.protection.temp_low_discharge

        logging.debug("logged to dbus ", round(self.battery.voltage / 100, 2),
                      round(self.battery.current / 100, 2),
                      round(self.battery.soc, 2))
