from utils import *
import jkbms
from battery import Protection, Battery, Cell




if __name__ == '__main__':
    print("Starte Test")
    bat = jkbms.Battery(1, 115200)
    bat.max_battery_charge_current = MAX_BATTERY_CHARGE_CURRENT
    bat.max_battery_discharge_current = MAX_BATTERY_DISCHARGE_CURRENT
    bat.cell_count = 3
    c1 = Cell(False)
    c1.voltage = 3.2
    bat.cells.append(c1)

    print("Mode: ", LIMITATION_MODE)

    for i in list(range(265, 315, 1)) + list(range(325, 365, 1)):
        c1.voltage = i / 100.0
        bat.manage_charge_current()
        print(f"c1.volt is: {c1.voltage:4.2f}V - CCL: {bat.control_charge_current:6.2f}A - DCL: {bat.control_discharge_current:6.2f}A")

    bat.temp1 = 25
    c1.voltage = 3.2
    for i in list(range(-25, 60, 1)):
        bat.temp2 = i
        bat.manage_charge_current()
        print(f"{c1.voltage=:4.2f}V - {bat.temp1=:3d}°C - {bat.temp2=:3d}°C -> {bat.get_temp()=:5.2f}°C - CCL: {bat.control_charge_current:6.2f}A - DCL: {bat.control_discharge_current:6.2f}A")



