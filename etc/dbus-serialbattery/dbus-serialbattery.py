#!/usr/bin/python
# -*- coding: utf-8 -*-
from typing import Union

from time import sleep
from dbus.mainloop.glib import DBusGMainLoop
from threading import Thread
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
from lltjbd import LltJbd
from daly import Daly
from ant import Ant
from jkbms import Jkbms

# from sinowealth import Sinowealth
from renogy import Renogy
from ecs import Ecs
from lifepower import Lifepower
from hlpdatabms4s import HLPdataBMS4S

supported_bms_types = [
    {'bms': HLPdataBMS4S, "baud": 9600},
    {"bms": LltJbd, "baud": 9600},
    {"bms": Ant, "baud": 19200},
    {"bms": Daly, "baud": 9600, "address": b"\x40"},
    {"bms": Daly, "baud": 9600, "address": b"\x80"},
    {"bms": Jkbms, "baud": 115200},
    #    {"bms" : Sinowealth},
    {"bms": Lifepower, "baud": 9600},
    {"bms": Renogy, "baud": 9600, "address": b"\x30"},
    {"bms": Renogy, "baud": 9600, "address": b"\xF7"},
    {"bms": Ecs, "baud": 19200},
]
expected_bms_types = [
    battery_type
    for battery_type in supported_bms_types
    if battery_type["bms"].__name__ == utils.BMS_TYPE or utils.BMS_TYPE == ""
]

logger.info("Starting dbus-serialbattery")


def main():
    def poll_battery(loop):
        # Run in separate thread. Pass in the mainloop so the thread can kill us if there is an exception.
        poller = Thread(target=lambda: helper.publish_battery(loop))
        # Thread will die with us if deamon
        poller.daemon = True
        poller.start()
        return True

    def get_battery(_port) -> Union[Battery, None]:
        # all the different batteries the driver support and need to test for
        # try to establish communications with the battery 3 times, else exit
        count = 3
        while count > 0:
            # create a new battery object that can read the battery and run connection test
            for test in expected_bms_types:
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
            count -= 1
            sleep(0.5)

        return None

    def get_port() -> str:
        # Get the port we need to use from the argument
        if len(sys.argv) > 1:
            return sys.argv[1]
        else:
            # just for MNB-SPI
            logger.info("No Port needed")
            return "/dev/tty/USB9"

    logger.info(
        "dbus-serialbattery v" + str(utils.DRIVER_VERSION) + utils.DRIVER_SUBVERSION
    )

    port = get_port()
    battery: Battery = get_battery(port)

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
