# -*- coding: utf-8 -*-
import asyncio
import atexit
import threading
from typing import Union, Optional

from bleak import BleakClient

from utils import *
from struct import *
from lltjbd import LltJbdProtection, LltJbd

BLE_SERVICE_UUID = "0000ff00-0000-1000-8000-00805f9b34fb"
BLE_CHARACTERISTICS_TX_UUID = "0000ff02-0000-1000-8000-00805f9b34fb"
BLE_CHARACTERISTICS_RX_UUID = "0000ff01-0000-1000-8000-00805f9b34fb"
MIN_RESPONSE_SIZE = 6
MAX_RESPONSE_SIZE = 256

class LltJbdBle(LltJbd):

    def __init__(self, port: str, baud: Optional[int], address: Optional[str]):
        super(LltJbdBle, self).__init__(port, -1, address)

        self.address = address
        self.protection = LltJbdProtection()
        self.type = self.BATTERYTYPE
        self.main_thread = threading.current_thread()
        self.bt_loop = asyncio.new_event_loop()
        self.data: bytearray = bytearray()
        self.run = True
        self.bt_thread = threading.Thread(name="BLELoop", target=self.background_loop, args=(self.bt_loop, ), daemon=True)
        self.bt_client: Optional[BleakClient] = None

    def on_disconnect(self, client):
        logger.info("BLE client disconnected")

    async def bt_main_loop(self):
        async with BleakClient(self.address, disconnected_callback=self.on_disconnect) as client:
            await client.start_notify(BLE_CHARACTERISTICS_RX_UUID, self.ncallback)
            await asyncio.sleep(1)
            self.bt_client = client
            self.name
            while self.run and client.is_connected and self.main_thread.is_alive():
                await asyncio.sleep(1)
            await client.stop_notify(BLE_CHARACTERISTICS_RX_UUID)

    def background_loop(self, loop: asyncio.AbstractEventLoop):
        asyncio.set_event_loop(loop)
        while self.run and self.main_thread.is_alive():
            loop.run_until_complete(self.bt_main_loop())
            sleep(0.01)
        loop.stop()

    def test_connection(self):
        if not self.address:
            return False

        if not self.bt_thread.is_alive():
            self.bt_thread.start()

            def shutdown_ble_atexit(thread):
                self.run = False
                thread.join()

            atexit.register(shutdown_ble_atexit, self.bt_thread)
        count = 0
        while not self.bt_client:
            count += 1
            sleep(0.2)
            if count == 10:
                return False
        return super().test_connection()

    def ncallback(self, sender, data: bytearray):
        self.data.extend(data)

    async def send_command(self, command) -> Union[bytearray, bool]:
        await self.bt_client.write_gatt_char(BLE_CHARACTERISTICS_TX_UUID, command, False)
        await asyncio.sleep(0.5)
        result = await self.read_bluetooth_data()
        return result

    async def read_bluetooth_data(
        self
    ) -> Union[bytearray, bool]:
        count = 0
        while len(self.data) < (self.LENGTH_POS + 1):
            await asyncio.sleep(0.01)
            count += 1
            if count > 50:
                break

        if len(self.data) < (self.LENGTH_POS + 1):
            if len(self.data) == 0:
                logger.error(">>> ERROR: No reply - returning")
            else:
                logger.error(
                    ">>> ERROR: No reply - returning [len:" + str(len(self.data)) + "]"
                )
            return False

        length = self.data[self.LENGTH_POS]
        count = 0
        while len(self.data) <= length + self.LENGTH_POS:
            await asyncio.sleep(0.005)
            count += 1
            if count > 150:
                logger.error(
                    ">>> ERROR: No reply - returning [len:"
                    + str(len(self.data))
                    + "/"
                    + str(length + self.LENGTH_POS)
                    + "]"
                )
                return False

        result = self.data
        self.data = bytearray()
        return result

    def read_serial_data_llt(self, command):
        task = asyncio.run_coroutine_threadsafe(self.send_command(command), self.bt_loop)
        try:
            data = task.result(timeout=2)
        except:
            logger.error(">>> ERROR: No reply - returning")
            return False
        if not data:
            return False

        start, flag, command_ret, length = unpack_from('BBBB', data)
        checksum, end = unpack_from('HB', data, length + 4)

        if end == 119:
            return data[4:length + 4]
        else:
            logger.error(">>> ERROR: Incorrect Reply")
            return False


async def testBLE():
    import sys
    bat = LltJbdBle("Foo", -1, sys.argv[1])
    if not bat.test_connection():
        logger.error(">>> ERROR: Unable to connect")
    else:
        bat.refresh_data()
    bat.refresh_data()
    bat.refresh_data()
    print("Done")


if __name__ == "__main__":
    asyncio.run(testBLE())

