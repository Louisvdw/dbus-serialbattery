# -*- coding: utf-8 -*-
from battery import Battery, Cell
from typing import Callable
from utils import logger
import utils
from time import sleep, time
from bms.jkbms_brn import Jkbms_Brn
import os

# from bleak import BleakScanner, BleakError
# import asyncio


class Jkbms_Ble(Battery):
    BATTERYTYPE = "Jkbms_Ble"
    resetting = False

    def __init__(self, port, baud, address):
        super(Jkbms_Ble, self).__init__(address.replace(":", "").lower(), baud, address)
        self.address = address
        self.type = self.BATTERYTYPE
        self.jk = Jkbms_Brn(address)
        self.unique_identifier_tmp = ""

        logger.info("Init of Jkbms_Ble at " + address)

    def connection_name(self) -> str:
        return "BLE " + self.address

    def custom_name(self) -> str:
        return "SerialBattery(" + self.type + ") " + self.address[-5:]

    def test_connection(self):
        # call a function that will connect to the battery, send a command and retrieve the result.
        # The result or call should be unique to this BMS. Battery name or version, etc.
        # Return True if success, False for failure
        result = False
        logger.info("Test of Jkbms_Ble at " + self.address)
        try:
            if self.address and self.address != "":
                result = True

            if result:
                # start scraping
                self.jk.start_scraping()
                tries = 1

                while self.jk.get_status() is None and tries < 20:
                    sleep(0.5)
                    tries += 1

                # load initial data, from here on get_status has valid values to be served to the dbus
                status = self.jk.get_status()

                if status is None:
                    self.jk.stop_scraping()
                    result = False

                if result and not status["device_info"]["vendor_id"].startswith(
                    ("JK-", "JK_")
                ):
                    self.jk.stop_scraping()
                    result = False

                # get first data to show in startup log
                if result:
                    self.get_settings()
                    self.refresh_data()
            if not result:
                logger.error("No BMS found at " + self.address)

        except Exception as err:
            logger.error(f"Unexpected {err=}, {type(err)=}")
            result = False

        return result

    def get_settings(self):
        # After successful  connection get_settings will be call to set up the battery.
        # Set the current limits, populate cell count, etc
        # Return True if success, False for failure
        st = self.jk.get_status()["settings"]
        self.cell_count = st["cell_count"]
        self.max_battery_charge_current = st["max_charge_current"]
        self.max_battery_discharge_current = st["max_discharge_current"]
        self.max_battery_voltage = st["cell_ovp"] * self.cell_count
        self.min_battery_voltage = st["cell_uvp"] * self.cell_count

        # "User Private Data" field in APP
        tmp = self.jk.get_status()["device_info"]["production"]
        self.custom_field = tmp if tmp != "Input Us" else None

        tmp = self.jk.get_status()["device_info"]["manufacturing_date"]
        self.production = "20" + tmp if tmp and tmp != "" else None

        self.unique_identifier_tmp = self.jk.get_status()["device_info"][
            "serial_number"
        ]

        for c in range(self.cell_count):
            self.cells.append(Cell(False))

        self.capacity = self.jk.get_status()["cell_info"]["capacity_nominal"]

        self.hardware_version = (
            "JKBMS "
            + self.jk.get_status()["device_info"]["hw_rev"]
            + " "
            + str(self.cell_count)
            + " cells"
            + (" (" + self.production + ")" if self.production else "")
        )
        logger.info("BAT: " + self.hardware_version)
        return True

    def unique_identifier(self) -> str:
        """
        Used to identify a BMS when multiple BMS are connected
        """
        return self.unique_identifier_tmp

    def use_callback(self, callback: Callable) -> bool:
        self.jk.set_callback(callback)
        return callback is not None

    def refresh_data(self):
        # call all functions that will refresh the battery data.
        # This will be called for every iteration (1 second)
        # Return True if success, False for failure

        # result = self.read_soc_data()
        # TODO: check for errors
        st = self.jk.get_status()
        if st is None:
            return False

        last_update = int(time() - st["last_update"])
        if last_update >= 15 and last_update % 15 == 0:
            logger.info(
                f"Jkbms_Ble: Bluetooth connection interrupted. Got no fresh data since {last_update}s."
            )
            # show Bluetooth signal strength (RSSI)
            bluetoothctl_info = os.popen(
                "bluetoothctl info "
                + self.address
                + ' | grep -i -E "device|name|alias|pair|trusted|blocked|connected|rssi|power"'
            )
            logger.info(bluetoothctl_info.read())
            bluetoothctl_info.close()

            # if the thread is still alive but data too old there is something
            # wrong with the bt-connection; restart whole stack
            if not self.resetting and last_update >= 60:
                logger.error(
                    "Jkbms_Ble: Bluetooth died. Restarting Bluetooth system driver."
                )
                self.reset_bluetooth()
                sleep(2)
                self.jk.start_scraping()
                sleep(2)

            return False
        else:
            self.resetting = False

        for c in range(self.cell_count):
            self.cells[c].voltage = st["cell_info"]["voltages"][c]

        self.to_temp(0, st["cell_info"]["temperature_mos"])
        self.to_temp(1, st["cell_info"]["temperature_sensor_1"])
        self.to_temp(2, st["cell_info"]["temperature_sensor_2"])
        self.current = round(st["cell_info"]["current"], 1)
        self.voltage = round(st["cell_info"]["total_voltage"], 2)

        self.soc = st["cell_info"]["battery_soc"]
        self.cycles = st["cell_info"]["cycle_count"]

        self.charge_fet = st["settings"]["charging_switch"]
        self.discharge_fet = st["settings"]["discharging_switch"]
        self.balance_fet = st["settings"]["balancing_switch"]

        self.balancing = False if st["cell_info"]["balancing_action"] == 0.000 else True
        self.balancing_current = (
            st["cell_info"]["balancing_current"]
            if st["cell_info"]["balancing_current"] < 32768
            else (65536 / 1000 - st["cell_info"]["balancing_current"]) * -1
        )
        self.balancing_action = st["cell_info"]["balancing_action"]

        # show wich cells are balancing
        for c in range(self.cell_count):
            if self.balancing and (
                st["cell_info"]["min_voltage_cell"] == c
                or st["cell_info"]["max_voltage_cell"] == c
            ):
                self.cells[c].balance = True
            else:
                self.cells[c].balance = False

        # protection bits
        # self.protection.soc_low = 2 if status["cell_info"]["battery_soc"] < 10.0 else 0

        # trigger cell imbalance warning when delta is to great
        if st["cell_info"]["delta_cell_voltage"] > min(
            st["settings"]["cell_ovp"] * 0.05, 0.200
        ):
            self.protection.cell_imbalance = 2
        elif st["cell_info"]["delta_cell_voltage"] > min(
            st["settings"]["cell_ovp"] * 0.03, 0.120
        ):
            self.protection.cell_imbalance = 1
        else:
            self.protection.cell_imbalance = 0

        self.protection.voltage_high = 2 if st["warnings"]["cell_overvoltage"] else 0
        self.protection.voltage_low = 2 if st["warnings"]["cell_undervoltage"] else 0

        self.protection.current_over = (
            2
            if (
                st["warnings"]["charge_overcurrent"]
                or st["warnings"]["discharge_overcurrent"]
            )
            else 0
        )
        self.protection.set_IC_inspection = (
            2 if st["cell_info"]["temperature_mos"] > 80 else 0
        )
        self.protection.temp_high_charge = 2 if st["warnings"]["charge_overtemp"] else 0
        self.protection.temp_low_charge = 2 if st["warnings"]["charge_undertemp"] else 0
        self.protection.temp_high_discharge = (
            2 if st["warnings"]["discharge_overtemp"] else 0
        )
        return True

    def reset_bluetooth(self):
        logger.info("Reset of system Bluetooth daemon triggered")
        self.resetting = True
        if self.jk.is_running():
            if self.jk.stop_scraping():
                logger.info("Scraping stopped, issuing sys-commands")
            else:
                logger.warning("Scraping was unable to stop, issuing sys-commands")

        # process kill is needed, since the service/bluetooth driver is probably freezed
        os.system('pkill -f "bluetoothd"')
        # stop will not work, if service/bluetooth driver is stuck
        # os.system("/etc/init.d/bluetooth stop")
        sleep(2)
        os.system("rfkill block bluetooth")
        os.system("rfkill unblock bluetooth")
        os.system("/etc/init.d/bluetooth start")
        logger.info("System Bluetooth daemon should have been restarted")

    def get_balancing(self):
        return 1 if self.balancing else 0

    def trigger_soc_reset(self):
        if utils.AUTO_RESET_SOC:
            self.jk.get_status()
            self.jk.trigger_soc_reset = True
        return
