#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
from time import sleep
from dbus.mainloop.glib import DBusGMainLoop
from threading import Thread
import dbus
import gobject
import logging
import sys

from dbushelper import DbusHelper
import battery
from lttjbd import LttJbd

# Constants - Need to dynamically get them in future
# update interval (ms)
INTERVAL = 1000

# Logging
logging.info('Starting dbus-serialbattery')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def main():

    def poll_battery(loop):
        # Run in separate thread. Pass in the mainloop so the thread can kill us if there is an exception.
        poller = Thread(target=lambda: helper.publish_battery(loop))
        # Tread will die with us if deamon
        poller.daemon = True
        poller.start()
        return True

    def get_battery_type(_port):
        # all the different batteries the driver support and need to test for
        battery_types = [
            LttJbd(port=_port, baud=9600)
        ]

        # try to establish communications with the battery 3 times, else exit
        count = 3
        while count > 0:
            # create a new battery object that can read the battery and run connection test
            for test in battery_types:
                if test.test_connection() is True:
                    return test

            count -= 1
            sleep(0.5)

        return None

    def get_port():
        # Get the port we need to use from the argument
        if len(sys.argv) > 1:
            return sys.argv[1]
        else:
            # just for testing purpose
            logger.info('No Port')
            return '/dev/ttyUSB2'

    logger.info('dbus-serialbattery')

    port = get_port()
    battery = get_battery_type(port)

    # exit if no battery could be found
    if battery is None:
        logger.error("ERROR >>> No battery connection at " + port)
        return

    # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
    DBusGMainLoop(set_as_default=True)
    gobject.threads_init()
    mainloop = gobject.MainLoop()

    # Get the initial values for the battery used by setup_vedbus
    helper = DbusHelper(battery)
    if not helper.setup_vedbus():
        logger.error("ERROR >>> Problem with battery set up at " + port)
        return
    logger.info('Battery connected to dbus from ' + port)


    # Poll the battery at INTERVAL and run the main loop
    gobject.timeout_add(INTERVAL, lambda: poll_battery(mainloop))
    try:
        mainloop.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
