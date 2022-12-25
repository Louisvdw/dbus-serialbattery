# -*- coding: utf-8 -*-
from battery import Protection, Battery, Cell
from utils import *
from struct import *
from jkbms import JkBmsBle
from bleak import BleakScanner

class Jkbms_Ble(Battery):
    BATTERYTYPE = "Jkbms BLE"
    def __init__(self, port,baud, address):
        super(Jkbms_Ble, self).__init__(port,baud)
        self.type = self.BATTERYTYPE
        self.jk = JkBmsBLE(address)


    def test_connection(self):
        # call a function that will connect to the battery, send a command and retrieve the result.
        # The result or call should be unique to this BMS. Battery name or version, etc.
        # Return True if success, False for failure
        
        # check if device with given mac is found, otherwise abort
        devices = await BleakScanner.discover()
        found=False
        for d in devices
            if d.address=self.jk.address
                found=True
        if not found:
            return False

        #device was found, presumeably a jkbms so start scraping
        jk.start_scraping()        
        tries = 1
        
        while jk.get_status() == None and tries < 20:
            time.sleep(0.5)
            tries += 1

        # load initial data, from here on get_status has valid values to be served to the dbus      
        status=jk.get_status()
        if status == None:
            return False
        
        if not status["device_info"]["vendor_id"].startswith("JK-")
            return False        
    
        logger.info("JK BMS found!")
        return true

    def get_settings(self):
        # After successful  connection get_settings will be call to set up the battery.
        # Set the current limits, populate cell count, etc
        # Return True if success, False for failure
        st=jk.get_status()["settings"]
        self.cell_count=st["cell_count"]
        self.max_battery_charge_current = st["max_charge_current"]
        self.max_battery_discharge_current = status["max_discharge_current"]
        self.max_battery_voltage = st["cell_ovp"] * self.cell_count
        self.min_battery_voltage = st["cell_uvp"] * self.cell_count

        for c in range(self.cell_count):
            self.cells.append(Cell(False))

        self.hardware_version = "JKBMS "+ jk.get_status()["device_info"]["hw_rev"]+" " + str(self.cell_count) + " cells" 

        return True

    def refresh_data(self):
        # call all functions that will refresh the battery data.
        # This will be called for every iteration (1 second)
        # Return True if success, False for failure
        
        #result = self.read_soc_data()
        #TODO: check for errors
        st=jk.get_status()
        if status == None:
            return False
        if time.time() - st["last_update"] > 30:
            #if data not updated for more than 30s, sth is wrong, then fail
            return False
          
        for c in range(self.cell_count):
            self.cells[c].voltage=st["cell_info"]["voltages"][c]
        
        self.to_temp(1, st["cell_info"]["temperature_sensor_1"])
        self.to_temp(2, st["cell_info"]["temperature_sensor_2"])
        self.current=st["cell_info"]["current"]
        self.voltage=st["cell_info"]["voltage"]

        self.soc=st["cell_info"]["battery_soc"]
        self.cycles=st["cell_info"]["cycle_count"]
        self.capacity=st["cell_info"]["nominal_capacity"]

        #protection bits
        #self.protection.soc_low = 2 if status["cell_info"]["battery_soc"] < 10.0 else 0
        #self.protection.cell_imbalance = 1 if status["warnings"]["cell_imbalance"] else 0
        
        self.protection.voltage_high = 2 if st["warnings"]["cell_overvoltage"] else 0
        self.protection.voltage_low = 2 if st["warnings"]["cell_undervoltage"] else 0
        
        self.protection.current_over = 2 if (st["warnings"]["charge_overcurrent"] or st["warnings"]["discharge_overcurrent"]) else 0
        
        self.protection.set_IC_inspection = 2 if st["warnings"]["temperature_mos"] else 0
        self.protection.temp_high_charge = 2 if st["warnings"]["charge_overtemp"] else 0
        self.protection.temp_low_charge = 2 if st["warnings"]["charge_undertemp"] else 0
        self.protection.temp_high_discharge = 2 if st["warnings"]["discharge_overtemp"] else 0
        return True
