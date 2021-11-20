from time import sleep
import logging
from renogy import Renogy

def get_battery_type(_port):
    # all the different batteries the driver support and need to test for
    battery_types = [
        #LltJbd(port=_port, baud=9600),
        #Ant(port=_port, baud=19200),
        #Daly(port=_port, baud=9600, address=b"\x40"),
        #Daly(port=_port, baud=9600, address=b"\x80"),
        #Jkbms(port=_port, baud=115200),
        #Sinowealth(port=_port, baud=9600),
        Renogy(port=_port, baud=9600)
        # MNB(port=_port, baud=9600),
    ]

    # try to establish communications with the battery 3 times, else exit
    count = 3
    while count > 0:
        # create a new battery object that can read the battery and run connection test
        for test in battery_types:
            print('Testing ' + test.__class__.__name__)
            if test.test_connection() is True:
                print('Connection established to ' + test.__class__.__name__)
                return test

        count -= 1
        sleep(0.5)

    return None

port = 'COM3'
battery = get_battery_type(port)

# exit if no battery could be found
if battery is None:
    print("ERROR >>> No battery connection at " + port)

battery.refresh_data()

print('test')