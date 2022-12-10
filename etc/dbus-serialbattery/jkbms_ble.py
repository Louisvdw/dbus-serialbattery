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
        
        # Uncomment if BMS does not supply capacity
        # self.capacity = BATTERY_CAPACITY
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
        status=jk.get_status()
        if status == None:
            return False
        if time.time() - status["last_update"] > 30:
            #if data not updated for more than 30s, sth is wrong, then fail
            return False
          
        for c in range(self.cell_count):
            self.cells[c].voltage=status["cell_info"]["voltages"][c]
        
        self.to_temp(1, status["cell_info"]["temperature_sensor_1"])
        self.to_temp(2, status["cell_info"]["temperature_sensor_2"])
        self.current=status["cell_info"]["current"]
        self.voltage=status["cell_info"]["voltage"]

        self.soc=status["cell_info"]["battery_soc"]
        self.cycles=status["cell_info"]["cycle_count"]
        self.capacity=status["cell_info"]["nominal_capacity"]
        return True


    def read_status_data(self):
        status_data = self.read_serial_data_template(self.command_status)
        # check if connection success
        if status_data is False:
            return False

        self.cell_count, self.temp_sensors, self.charger_connected, self.load_connected, \
            state, self.cycles = unpack_from('>bb??bhx', status_data)

        self.hardware_version = "TemplateBMS " + str(self.cell_count) + " cells"
        logger.info(self.hardware_version)
        return True

    def read_soc_data(self):
        soc_data = self.read_serial_data_template(self.command_soc)
        # check if connection success
        if soc_data is False:
            return False

        voltage, current, soc = unpack_from('>hxxhh', soc_data)
        self.voltage = voltage / 10
        self.current = current / -10
        self.soc = soc / 10
        return True

    def read_serial_data_template(self, command):
        # use the read_serial_data() function to read the data and then do BMS spesific checks (crc, start bytes, etc)
        data = read_serial_data(command, self.port, self.baud_rate, self.LENGTH_POS, self.LENGTH_CHECK)
        if data is False:
            return False

        start, flag, command_ret, length = unpack_from('BBBB', data)
        checksum = sum(data[:-1]) & 0xFF

        if start == 165 and length == 8 and checksum == data[12]:
            return data[4:length+4]
        else:
            logger.error(">>> ERROR: Incorrect Reply")
            return False
