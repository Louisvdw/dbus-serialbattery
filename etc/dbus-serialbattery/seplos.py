# -*- coding: utf-8 -*-
from battery import Protection, Battery, Cell
from utils import *


def int_from_hex_ascii(to_decode, signed=False):
    return int.from_bytes(bytes.fromhex(to_decode.decode('ascii')), byteorder="big", signed=signed)


class Seplos(Battery):
    def __init__(self, port, baud, address):
        super(Seplos, self).__init__(port, baud, address)
        self.type = self.BATTERYTYPE

    BATTERYTYPE = "Seplos"

    LENGTH_POS = 10

    # TODO: use address parameter in command
    comm_start = b"\x7e"
    comm_version = b"\x32\x30"  # 20
    comm_addr = b"\x30\x30"  # 00
    comm_cid1 = b"\x34\x36"  # 46
    comm_cid2 = b"\x34\x32"  # 42
    comm_length = b"\x45\x30\x30\x32"
    comm_datainfo = b"\x30\x31"
    comm_chksum = b"\x46\x44\x33\x36"
    comm_end = b"\x0d"

    command_status = comm_start \
                 + comm_version \
                 + comm_addr \
                 + comm_cid1 \
                 + comm_cid2 \
                 + comm_length + comm_datainfo + comm_chksum + comm_end

    def test_connection(self):
        # call a function that will connect to the battery, send a command and retrieve the result.
        # The result or call should be unique to this BMS. Battery name or version, etc.
        # Return True if success, False for failure

        try:
            return self.read_status_data()
        except Exception as err:
            logger.error(f"Unexpected {err=}, {type(err)=}")
            return False

    def get_settings(self):
        # After successful  connection get_settings will be call to set up the battery.
        # Set the current limits, populate cell count, etc.
        # Return True if success, False for failure

        # Uncomment if BMS does not supply capacity
        # self.capacity = BATTERY_CAPACITY
        self.max_battery_charge_current = MAX_BATTERY_CHARGE_CURRENT
        self.max_battery_discharge_current = MAX_BATTERY_DISCHARGE_CURRENT
        self.max_battery_voltage = MAX_CELL_VOLTAGE * self.cell_count
        self.min_battery_voltage = MIN_CELL_VOLTAGE * self.cell_count

        # init the cell array
        for _ in range(self.cell_count):
            self.cells.append(Cell(False))

        # self.hardware_version = "Seplos BMS " + str(self.cell_count) + " cells"
        return True

    def refresh_data(self):
        # call all functions that will refresh the battery data.
        # This will be called for every iteration (1 second)
        # Return True if success, False for failure
        result = self.read_status_data()

        return result

    def read_status_data(self):
        logger.info("read status data")
        data = self.read_serial_data_seplos(self.command_status)
        # check if connection success
        if data is False:
            return False

        self.cell_count = int_from_hex_ascii(data[4:6])
        voltage_offset = 6
        if self.cell_count == len(self.cells):
            for i in range(self.cell_count):
                v = int_from_hex_ascii(data[voltage_offset + i*4 : voltage_offset + i*4 + 4 ]) / 1000
                logger.info("voltage cell[" + str(i) + "]=" + str(v))
                self.cells[i].voltage = v

        temps_offset = 72
        if self.cell_count == len(self.cells):
            for i in range(4):
                t = (int_from_hex_ascii(data[temps_offset + i * 4: temps_offset + i * 4 + 4]) - 2731) / 10
                self.cells[i].temp = t
                logger.info("temp cell[" + str(i) + "]=" + str(t))
        self.temp1 = (int_from_hex_ascii(data[72 + 4*4 : 72 + 4*4 + 4]) - 2731) / 10
        self.temp2 = (int_from_hex_ascii(data[72 + 5*4 : 72 + 5*4 + 4]) - 2731) / 10
        logger.info("Environment temp = " + str(self.temp1) + " Power temp = " + str(self.temp2))

        self.current = int_from_hex_ascii(data[96:100], signed=True)/100
        self.voltage = int_from_hex_ascii(data[100:104])/100
        logger.info("Current = " + str(self.current) + " Voltage = " + str(self.voltage))

        self.capacity_remain = int_from_hex_ascii(data[104:108])/100
        self.capacity        = int_from_hex_ascii(data[110:114])/100
        self.soc             = int_from_hex_ascii(data[114:118])/10
        logger.info("Capacity = " + str(self.capacity_remain) + "/" + str(self.capacity) + " SOC = " + str(self.soc))

        self.cycles          = int_from_hex_ascii(data[122:126])
        logger.debug("Cycles = " + str(self.cycles))

        self.hardware_version = "Seplos BMS " + str(self.cell_count) + " cells"
        logger.info(self.hardware_version)

        # TODO: read alarms?
        return True

    def read_serial_data_seplos(self, command):
        logger.info("read serial data seplos")

        with serial.Serial(self.port, baudrate=self.baud_rate, timeout=1) as ser:
            # TODO: revisit timing problems
            ser.flushOutput()
            ser.flushInput()
            written = ser.write(command)
            logger.info("wrote " + str(written) + " bytes to serialport, command=" + str(command))

            count = 0
            toread = ser.inWaiting()

            while toread < self.LENGTH_POS + 4: # need to read at least until the 4 Byte length information are available
                sleep(0.1)
                toread = ser.inWaiting()
                count += 1
                if count > 20:
                    logger.error(">>> ERROR: No reply - returning")
                    return False

            bytes_read = ser.read(toread)
            # we can now decode the length, it is encoded in 4 ascii bytes, first byte is lchksum, rest is actual length
            # XXX: verify LENGTH CHECKSUM, ignoring it for now
            length = int_from_hex_ascii( b"0" + bytes_read[self.LENGTH_POS:self.LENGTH_POS + 3] )

            # length is the number of bytes in INFO, total response length is length + 18
            total_length = length + 18
            logger.info("decoded length=" + str(length) + " total_length=" + str(total_length))

            data = bytearray(bytes_read)
            count = 0
            while len(data) < total_length:
                res = ser.read(total_length)
                data.extend(res)
                logger.info('serial data length ' + str(len(data)))
                sleep(0.005)
                count += 1
                if count > 150:
                    logger.error( ">>> ERROR: No reply - returning [len:" + str(len(data)) + "/" + str(total_length) + "]" )
                    return False

            # XXX check validity of result: return code, checksum
            return_data = data[self.LENGTH_POS + 3:self.LENGTH_POS + 3 + length]
            logger.info("returning data: " + return_data.decode('ascii'))
            return return_data