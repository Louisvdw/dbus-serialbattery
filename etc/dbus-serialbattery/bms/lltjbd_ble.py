# -*- coding: utf-8 -*-
import asyncio
import atexit
import functools
import threading
from typing import Union, Optional
from utils import logger
from struct import unpack_from
from bleak import BleakClient, BleakScanner, BLEDevice
from bms.lltjbd import LltJbdProtection, LltJbd, checksum

BLE_SERVICE_UUID = "0000ff00-0000-1000-8000-00805f9b34fb"
BLE_CHARACTERISTICS_TX_UUID = "0000ff02-0000-1000-8000-00805f9b34fb"
BLE_CHARACTERISTICS_RX_UUID = "0000ff01-0000-1000-8000-00805f9b34fb"
MIN_RESPONSE_SIZE = 6
MAX_RESPONSE_SIZE = 256


class LltJbd_Ble(LltJbd):
    BATTERYTYPE = "LltJbd_Ble"

    def __init__(self, port: Optional[str], baud: Optional[int], address: str):
        super(LltJbd_Ble, self).__init__(address.replace(":", "").lower(), -1, address)

        self.address = address
        self.protection = LltJbdProtection()
        self.type = self.BATTERYTYPE
        self.main_thread = threading.current_thread()
        self.data: bytearray = bytearray()
        self.run = True
        self.bt_thread = threading.Thread(
            name="LltJbd_Ble_Loop", target=self.background_loop, daemon=True
        )
        self.bt_loop: Optional[asyncio.AbstractEventLoop] = None
        self.bt_client: Optional[BleakClient] = None
        self.device: Optional[BLEDevice] = None
        self.response_queue: Optional[asyncio.Queue] = None
        self.ready_event: Optional[asyncio.Event] = None

        logger.info("Init of LltJbd_Ble at " + address)

    def connection_name(self) -> str:
        return "BLE " + self.address

    def custom_name(self) -> str:
        return self.device.name

    def on_disconnect(self, client):
        logger.info("BLE client disconnected")

    async def bt_main_loop(self):
        self.device = await BleakScanner.find_device_by_address(
            self.address, cb=dict(use_bdaddr=True)
        )

        if not self.device:
            self.run = False
            return

        async with BleakClient(
            self.device, disconnected_callback=self.on_disconnect
        ) as client:
            self.bt_client = client
            self.bt_loop = asyncio.get_event_loop()
            self.response_queue = asyncio.Queue()
            self.ready_event.set()
            while self.run and client.is_connected and self.main_thread.is_alive():
                await asyncio.sleep(0.1)
        self.bt_loop = None

    def background_loop(self):
        while self.run and self.main_thread.is_alive():
            asyncio.run(self.bt_main_loop())

    async def async_test_connection(self):
        self.ready_event = asyncio.Event()
        if not self.bt_thread.is_alive():
            self.bt_thread.start()

            def shutdown_ble_atexit(thread):
                self.run = False
                thread.join()

            atexit.register(shutdown_ble_atexit, self.bt_thread)
        try:
            return await asyncio.wait_for(self.ready_event.wait(), timeout=5)
        except asyncio.TimeoutError:
            logger.error(">>> ERROR: Unable to connect with BLE device")
            return False

    def test_connection(self):
        # call a function that will connect to the battery, send a command and retrieve the result.
        # The result or call should be unique to this BMS. Battery name or version, etc.
        # Return True if success, False for failure
        result = False
        logger.info("Test of LltJbd_Ble at " + self.address)
        try:
            if self.address:
                result = True
            if result and asyncio.run(self.async_test_connection()):
                result = True
            if result:
                result = super().test_connection()
            if not result:
                logger.error("No BMS found at " + self.address)
        except Exception as err:
            logger.error(f"Unexpected {err=}, {type(err)=}")
            result = False

        return result

    async def send_command(self, command) -> Union[bytearray, bool]:
        if not self.bt_client:
            logger.error(">>> ERROR: No BLE client connection - returning")
            return False

        fut = self.bt_loop.create_future()

        def rx_callback(future: asyncio.Future, data: bytearray, sender, rx: bytearray):
            data.extend(rx)
            if len(data) < (self.LENGTH_POS + 1):
                return

            length = data[self.LENGTH_POS]
            if len(data) <= length + self.LENGTH_POS + 1:
                return
            if not future.done():
                future.set_result(data)

        rx_collector = functools.partial(rx_callback, fut, bytearray())
        await self.bt_client.start_notify(BLE_CHARACTERISTICS_RX_UUID, rx_collector)
        await self.bt_client.write_gatt_char(
            BLE_CHARACTERISTICS_TX_UUID, command, False
        )
        result = await fut
        await self.bt_client.stop_notify(BLE_CHARACTERISTICS_RX_UUID)

        return result

    async def async_read_serial_data_llt(self, command):
        try:
            bt_task = asyncio.run_coroutine_threadsafe(
                self.send_command(command), self.bt_loop
            )
            result = await asyncio.wait_for(asyncio.wrap_future(bt_task), 20)
            return result
        except asyncio.TimeoutError:
            logger.error(">>> ERROR: No reply - returning")
            return False
        except Exception as e:
            logger.error(">>> ERROR: No reply - returning", e)
            return False

    def read_serial_data_llt(self, command):
        if not self.bt_loop:
            return False
        data = asyncio.run(self.async_read_serial_data_llt(command))
        return self.validate_packet(data)


if __name__ == "__main__":
    import sys

    bat = LltJbd_Ble("Foo", -1, sys.argv[1])
    if not bat.test_connection():
        logger.error(">>> ERROR: Unable to connect")
    else:
        bat.refresh_data()
        bat.get_settings()
