#!/usr/bin/python
# -*- coding: utf-8 -*-
from typing import Union

from time import sleep
from dbus.mainloop.glib import DBusGMainLoop

# from threading import Thread  ## removed with https://github.com/Louisvdw/dbus-serialbattery/pull/582
import sys

if sys.version_info.major == 2:
    import gobject
else:
    from gi.repository import GLib as gobject

# Victron packages
# from ve_utils import exit_on_error

from dbushelper import DbusHelper
from utils import logger
import utils
from battery import Battery

# import battery classes
from bms.daly import Daly
from bms.ecs import Ecs
from bms.heltecmodbus import HeltecModbus
from bms.hlpdatabms4s import HLPdataBMS4S
from bms.jkbms import Jkbms
from bms.lifepower import Lifepower
from bms.lltjbd import LltJbd
from bms.renogy import Renogy
from bms.seplos import Seplos

# from bms.ant import Ant
# from bms.mnb import MNB
# from bms.sinowealth import Sinowealth

supported_bms_types = [
    {"bms": Daly, "baud": 9600, "address": b"\x40"},
    {"bms": Daly, "baud": 9600, "address": b"\x80"},
    {"bms": Ecs, "baud": 19200},
    {"bms": HeltecModbus, "baud": 9600},
    {"bms": HLPdataBMS4S, "baud": 9600},
    {"bms": Jkbms, "baud": 115200},
    {"bms": Lifepower, "baud": 9600},
    {"bms": LltJbd, "baud": 9600},
    {"bms": Renogy, "baud": 9600, "address": b"\x30"},
    {"bms": Renogy, "baud": 9600, "address": b"\xF7"},
    {"bms": Seplos, "baud": 19200},
    # {"bms": Ant, "baud": 19200},
    # {"bms": MNB, "baud": 9600},
    # {"bms": Sinowealth},
]
expected_bms_types = [
    battery_type
    for battery_type in supported_bms_types
    if battery_type["bms"].__name__ == utils.BMS_TYPE or utils.BMS_TYPE == ""
]

print("")
logger.info("Starting dbus-serialbattery")


def main():
    def poll_battery(loop):
        helper.publish_battery(loop)
        return True

    def get_battery(_port) -> Union[Battery, None]:
        # all the different batteries the driver support and need to test for
        # try to establish communications with the battery 3 times, else exit
        count = 3
        while count > 0:
            # create a new battery object that can read the battery and run connection test
            for test in expected_bms_types:
                # noinspection PyBroadException
                try:
                    logger.info("Testing " + test["bms"].__name__)
                    batteryClass = test["bms"]
                    baud = test["baud"]
                    battery: Battery = batteryClass(
                        port=_port, baud=baud, address=test.get("address")
                    )
                    if battery.test_connection():
                        logger.info(
                            "Connection established to " + battery.__class__.__name__
                        )
                        return battery
                except KeyboardInterrupt:
                    return None
                except Exception:
                    # Ignore any malfunction test_function()
                    pass
            count -= 1
            sleep(0.5)

        return None

    def get_port() -> str:
        # Get the port we need to use from the argument
        if len(sys.argv) > 1:
            port = sys.argv[1]
            if port not in utils.EXCLUDED_DEVICES:
                return port
            else:
                logger.info(
                    "Stopping dbus-serialbattery: "
                    + str(port)
                    + " is excluded trough the config file"
                )
                sleep(86400)
                sys.exit(0)
        else:
            # just for MNB-SPI
            logger.info("No Port needed")
            return "/dev/tty/USB9"

    logger.info("dbus-serialbattery v" + str(utils.DRIVER_VERSION))

    port = get_port()
    battery = None
    if port.endswith("_Ble") and len(sys.argv) > 2:
        """
        Import ble classes only, if it's a ble port, else the driver won't start due to missing python modules
        This prevent problems when using the driver only with a serial connection
        """
        if port == "Jkbms_Ble":
            # noqa: F401 --> ignore flake "imported but unused" error
            from bms.jkbms_ble import Jkbms_Ble  # noqa: F401

        if port == "LltJbd_Ble":
            # noqa: F401 --> ignore flake "imported but unused" error
            from bms.lltjbd_ble import LltJbd_Ble  # noqa: F401

        class_ = eval(port)
        testbms = class_("", 9600, sys.argv[2])
        if testbms.test_connection() is True:
            logger.info("Connection established to " + testbms.__class__.__name__)
            battery = testbms
    else:
        battery = get_battery(port)

    # exit if no battery could be found
    if battery is None:
        logger.error("ERROR >>> No battery connection at " + port)
        sys.exit(1)

    battery.log_settings()

    # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
    DBusGMainLoop(set_as_default=True)
    if sys.version_info.major == 2:
        gobject.threads_init()
    mainloop = gobject.MainLoop()

    # Get the initial values for the battery used by setup_vedbus
    helper = DbusHelper(battery)

    if not helper.setup_vedbus():
        logger.error("ERROR >>> Problem with battery set up at " + port)
        sys.exit(1)

    # Poll the battery at INTERVAL and run the main loop
    gobject.timeout_add(battery.poll_interval, lambda: poll_battery(mainloop))
    try:
        mainloop.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
