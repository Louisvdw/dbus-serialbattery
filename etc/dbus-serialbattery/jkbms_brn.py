import asyncio
from bleak import BleakScanner, BleakClient
import time
from logging import info, debug
import logging
from struct import unpack_from, calcsize
import threading

logging.basicConfig(level=logging.INFO)


# zero means parse all incoming data (every second)
CELL_INFO_REFRESH_S = 0
DEVICE_INFO_REFRESH_S = 60 * 60 * 5  # every 5 Hours
CHAR_HANDLE = "0000ffe1-0000-1000-8000-00805f9b34fb"
MODEL_NBR_UUID = "00002a24-0000-1000-8000-00805f9b34fb"

COMMAND_CELL_INFO = 0x96
COMMAND_DEVICE_INFO = 0x97

FRAME_VERSION_JK04 = 0x01
FRAME_VERSION_JK02 = 0x02
FRAME_VERSION_JK02_32S = 0x03
PROTOCOL_VERSION_JK02 = 0x02


protocol_version = PROTOCOL_VERSION_JK02


MIN_RESPONSE_SIZE = 300
MAX_RESPONSE_SIZE = 320

TRANSLATE_DEVICE_INFO = [
    [["device_info", "hw_rev"], 22, "8s"],
    [["device_info", "sw_rev"], 30, "8s"],
    [["device_info", "uptime"], 38, "<L"],
    [["device_info", "vendor_id"], 6, "16s"],
    [["device_info", "manufacturing_date"], 78, "8s"],
]

TRANSLATE_SETTINGS = [
    [["settings", "cell_uvp"], 10, "<L", 0.001],
    [["settings", "cell_uvpr"], 14, "<L", 0.001],
    [["settings", "cell_ovp"], 18, "<L", 0.001],
    [["settings", "cell_ovpr"], 22, "<L", 0.001],
    [["settings", "balance_trigger_voltage"], 26, "<L", 0.001],
    [["settings", "power_off_voltage"], 46, "<L", 0.001],
    [["settings", "max_charge_current"], 50, "<L", 0.001],
    [["settings", "max_discharge_current"], 62, "<L", 0.001],
    [["settings", "max_balance_current"], 50, "<L", 0.001],
    [["settings", "cell_count"], 114, "<L"],
    [["settings", "charging_switch"], 118, "4?"],
    [["settings", "discharging_switch"], 122, "4?"],
    [["settings", "balancing_switch"], 126, "4?"],
]


TRANSLATE_CELL_INFO = [
    [["cell_info", "voltages", 16], 6, "<H", 0.001],
    [["cell_info", "average_cell_voltage"], 58, "<H", 0.001],
    [["cell_info", "delta_cell_voltage"], 60, "<H", 0.001],
    [["cell_info", "max_voltage_cell"], 62, "<B"],
    [["cell_info", "min_voltage_cell"], 63, "<B"],
    [["cell_info", "resistances", 16], 64, "<H", 0.001],
    [["cell_info", "total_voltage"], 118, "<H", 0.001],
    [["cell_info", "current"], 126, "<l", 0.001],
    [["cell_info", "temperature_sensor_1"], 130, "<H", 0.1],
    [["cell_info", "temperature_sensor_2"], 132, "<H", 0.1],
    [["cell_info", "temperature_mos"], 134, "<H", 0.1],
    [["cell_info", "balancing_current"], 138, "<H", 0.001],
    [["cell_info", "balancing_action"], 140, "<B", 0.001],
    [["cell_info", "battery_soc"], 141, "B"],
    [["cell_info", "capacity_remain"], 142, "<L", 0.001],
    [["cell_info", "capacity_nominal"], 146, "<L", 0.001],
    [["cell_info", "cycle_count"], 150, "<L"],
    [["cell_info", "cycle_capacity"], 154, "<L", 0.001],
    [["cell_info", "charging_switch_enabled"], 166, "1?"],
    [["cell_info", "discharging_switch_enabled"], 167, "1?"],
    [["cell_info", "balancing_active"], 191, "1?"],
]


class JkBmsBle:
    # entries for translating the bytearray to py-object via unpack
    # [[py dict entry as list, each entry ] ]

    frame_buffer = bytearray()
    bms_status = {}

    waiting_for_responsei = ""
    last_cell_info = 0

    def __init__(self, addr):
        self.address = addr
        self.bt_thread = threading.Thread(target=self.connect_and_scrape)

    async def scanForDevices(self):
        devices = await BleakScanner.discover()
        for d in devices:
            print(d)

    # iterative implementation maybe later due to referencing
    def translate(self, fb, translation, o, i=0):
        if i == len(translation[0]) - 1:
            # keep things universal by using an n=1 list
            kees = (
                range(0, translation[0][i])
                if isinstance(translation[0][i], int)
                else [translation[0][i]]
            )
            i = 0
            for j in kees:
                if isinstance(translation[2], int):
                    # handle raw bytes without unpack_from;
                    # 3. param gives no format but number of bytes
                    val = bytearray(
                        fb[translation[1] + i : translation[1] + i + translation[2]]
                    )
                    i += translation[2]
                else:
                    val = unpack_from(
                        translation[2], bytearray(fb), translation[1] + i
                    )[0]
                    # calculate stepping in case of array
                    i = i + calcsize(translation[2])
                if isinstance(val, bytes):
                    val = val.decode("utf-8").rstrip(" \t\n\r\0")
                elif isinstance(val, int) and len(translation) == 4:
                    val = val * translation[3]
                o[j] = val
        else:
            if translation[0][i] not in o:
                if len(translation[0]) == i + 2 and isinstance(
                    translation[0][i + 1], int
                ):
                    o[translation[0][i]] = [None] * translation[0][i + 1]
                else:
                    o[translation[0][i]] = {}

            self.translate(fb, translation, o[translation[0][i]], i + 1)

    def decode_warnings(self, fb):
        val = unpack_from("<H", bytearray(fb), 136)[0]

        self.bms_status["cell_info"]["error_bitmask_16"] = hex(val)
        self.bms_status["cell_info"]["error_bitmask_2"] = format(val, "016b")

        if "warnings" not in self.bms_status:
            self.bms_status["warnings"] = {}

        self.bms_status["warnings"]["resistance_too_high"] = bool(val & (1 << 0))
        self.bms_status["warnings"]["cell_count_wrong"] = bool(val & (1 << 2))  # ?
        self.bms_status["warnings"]["charge_overtemp"] = bool(val & (1 << 8))
        self.bms_status["warnings"]["charge_undertemp"] = bool(val & (1 << 9))
        self.bms_status["warnings"]["discharge_overtemp"] = bool(val & (1 << 15))
        self.bms_status["warnings"]["cell_overvoltage"] = bool(val & (1 << 4))
        self.bms_status["warnings"]["cell_undervoltage"] = bool(val & (1 << 11))
        self.bms_status["warnings"]["charge_overcurrent"] = bool(val & (1 << 6))
        self.bms_status["warnings"]["discharge_overcurrent"] = bool(val & (1 << 13))
        # bis hierhin verifiziert, rest zu testen

    def decode_device_info_jk02(self):
        fb = self.frame_buffer
        for t in TRANSLATE_DEVICE_INFO:
            self.translate(fb, t, self.bms_status)

    def decode_cellinfo_jk02(self):
        fb = self.frame_buffer
        for t in TRANSLATE_CELL_INFO:
            self.translate(fb, t, self.bms_status)
        self.decode_warnings(fb)
        debug(self.bms_status)

    def decode_settings_jk02(self):
        fb = self.frame_buffer
        for t in TRANSLATE_SETTINGS:
            self.translate(fb, t, self.bms_status)
        debug(self.bms_status)

    def decode(self):
        # check what kind of info the frame contains
        info_type = self.frame_buffer[4]
        if info_type == 0x01:
            info("Processing frame with settings info")
            if protocol_version == PROTOCOL_VERSION_JK02:
                self.decode_settings_jk02()
                self.bms_status["last_update"] = time.time()

        elif info_type == 0x02:
            if (
                CELL_INFO_REFRESH_S == 0
                or time.time() - self.last_cell_info > CELL_INFO_REFRESH_S
            ):
                self.last_cell_info = time.time()
                info("processing frame with battery cell info")
                if protocol_version == PROTOCOL_VERSION_JK02:
                    self.decode_cellinfo_jk02()
                    self.bms_status["last_update"] = time.time()
                # power is calculated from voltage x current as
                # register 122 contains unsigned power-value
                self.bms_status["cell_info"]["power"] = (
                    self.bms_status["cell_info"]["current"]
                    * self.bms_status["cell_info"]["total_voltage"]
                )
                if self.waiting_for_response == "cell_info":
                    self.waiting_for_response = ""

        elif info_type == 0x03:
            info("processing frame with device info")
            if protocol_version == PROTOCOL_VERSION_JK02:
                self.decode_device_info_jk02()
                self.bms_status["last_update"] = time.time()
            else:
                return
            if self.waiting_for_response == "device_info":
                self.waiting_for_response = ""

    def assemble_frame(self, data: bytearray):
        if len(self.frame_buffer) > MAX_RESPONSE_SIZE:
            info("data dropped because it alone was longer than max frame length")
            self.frame_buffer = []

        if data[0] == 0x55 and data[1] == 0xAA and data[2] == 0xEB and data[3] == 0x90:
            # beginning of new frame, clear buffer
            self.frame_buffer = []

        self.frame_buffer.extend(data)

        if len(self.frame_buffer) >= MIN_RESPONSE_SIZE:
            # check crc; always at position 300, independent of
            # actual frame-lentgh, so crc up to 299
            ccrc = self.crc(self.frame_buffer, 300 - 1)
            rcrc = self.frame_buffer[300 - 1]
            debug(f"compair recvd. crc: {rcrc} vs calc. crc: {ccrc}")
            if ccrc == rcrc:
                debug("great success! frame complete and sane, lets decode")
                self.decode()
                self.frame_buffer = []

    def ncallback(self, sender: int, data: bytearray):
        debug(f"------> NEW PACKAGE!laenge:  {len(data)}")
        self.assemble_frame(data)

    def crc(self, arr: bytearray, length: int) -> int:
        crc = 0
        for a in arr[:length]:
            crc = crc + a
        return crc.to_bytes(2, "little")[0]

    async def write_register(
        self, address, vals: bytearray, length: int, bleakC: BleakClient
    ):
        frame = bytearray(20)
        frame[0] = 0xAA  # start sequence
        frame[1] = 0x55  # start sequence
        frame[2] = 0x90  # start sequence
        frame[3] = 0xEB  # start sequence
        frame[4] = address  # holding register
        frame[5] = length  # size of the value in byte
        frame[6] = vals[0]
        frame[7] = vals[1]
        frame[8] = vals[2]
        frame[9] = vals[3]
        frame[10] = 0x00
        frame[11] = 0x00
        frame[12] = 0x00
        frame[13] = 0x00
        frame[14] = 0x00
        frame[15] = 0x00
        frame[16] = 0x00
        frame[17] = 0x00
        frame[18] = 0x00
        frame[19] = self.crc(frame, len(frame) - 1)
        debug("Write register: ", frame)
        await bleakC.write_gatt_char(CHAR_HANDLE, frame, False)

    async def request_bt(self, rtype: str, client):
        timeout = time.time()

        while self.waiting_for_response != "" and time.time() - timeout < 10:
            await asyncio.sleep(1)
            print(self.waiting_for_response)

        if rtype == "cell_info":
            cmd = COMMAND_CELL_INFO
            self.waiting_for_response = "cell_info"
        elif rtype == "device_info":
            cmd = COMMAND_DEVICE_INFO
            self.waiting_for_response = "device_info"
        else:
            return

        await self.write_register(cmd, b"\0\0\0\0", 0x00, client)

    def get_status(self):
        if "settings" in self.bms_status and "cell_info" in self.bms_status:
            return self.bms_status
        else:
            return None

    def connect_and_scrape(self):
        asyncio.run(self.asy_connect_and_scrape())

    async def asy_connect_and_scrape(self):
        print("connect and scrape on address: " + self.address)
        self.run = True
        while self.run and self.main_thread.is_alive():  # autoreconnect
            client = BleakClient(self.address)
            print("btloop")
            try:
                await client.connect()
                self.bms_status["model_nbr"] = (
                    await client.read_gatt_char(MODEL_NBR_UUID)
                ).decode("utf-8")

                await client.start_notify(CHAR_HANDLE, self.ncallback)
                await self.request_bt("device_info", client)

                await self.request_bt("cell_info", client)
                # await self.enable_charging(client)
                last_dev_info = time.time()
                while client.is_connected and self.run and self.main_thread.is_alive():
                    if time.time() - last_dev_info > DEVICE_INFO_REFRESH_S:
                        last_dev_info = time.time()
                        await self.request_bt("device_info", client)
                    await asyncio.sleep(0.01)
            except Exception as e:
                info("error while connecting to bt: " + str(e))
                self.run = False
            finally:
                await client.disconnect()

        print("Exiting bt-loop")

    def start_scraping(self):
        self.main_thread = threading.current_thread()
        if self.is_running():
            return
        self.bt_thread.start()
        info(
            "scraping thread started -> main thread id: "
             + str(self.main_thread.ident)
             + " scraping thread: "
             + str(self.bt_thread.ident)
        )

    def stop_scraping(self):
        self.run = False
        while self.is_running():
            time.sleep(0.1)

    def is_running(self):
        return self.bt_thread.is_alive()

    async def enable_charging(self, c):
        # these are the registers for the control-buttons:
        # data is 01 00 00 00 for on  00 00 00 00 for off;
        # the following bytes up to 19 are unclear and changing
        # dynamically -> auth-mechanism?
        await self.write_register(0x1D, b"\x01\x00\x00\x00", 4, c)
        await self.write_register(0x1E, b"\x01\x00\x00\x00", 4, c)
        await self.write_register(0x1F, b"\x01\x00\x00\x00", 4, c)
        await self.write_register(0x40, b"\x01\x00\x00\x00", 4, c)


if __name__ == "__main__":
    jk = JkBmsBle("C8:47:8C:E4:54:0E")
    info("sss")
    jk.start_scraping()
    while True:
        print("asdf")
        print(jk.get_status())
        time.sleep(5)
