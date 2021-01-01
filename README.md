# dbus-serialbattery
This is a driver for VenusOS devices (any GX device sold by Victron or a Raspberry Pi running the VenusOS image). 

The driver will communicate with a Battery Management System (BMS) that support serial communication (RS232 or RS485) 
and publish this data to the dbus used by VenusOS. The main purpose is to supply up to date State Of Charge (SOC) values
to the inverter, but many extra parameters is also published if available from the BMS.

Driver support:
 * Smart BMS range from [LLT Power](https://www.lithiumbatterypcb.com/product-instructionev-battery-pcb-boardev-battery-pcb-board/ev-battery-pcb-board/smart-bms-of-power-battery/) / [Jiabaida BMS](https://dgjbd.en.alibaba.com/)
(Cell values are currently only supported for the first 16 cells: Min Cell V, Max Cell V, Cell Balance) 

Planned support:
 * AntBMS
 * Smart Daly BMS 

### How to install
1. You need to have a VenusOS device set up and running on your system and have [root access](https://www.victronenergy.com/live/ccgx:root_access).
2. You also need to connect your BMS to the VenusOS device using a serial interface. A USB->232 converter like the FT232R. The FT232R already has a driver included in the VenusOS. Only connect the Ground, Rx & Tx to the BMS.
3. Use a FTP client that support SFTP to copy the driver files to the rooted VenusOS device. [Filezilla](https://filezilla-project.org/) is a good option
   - copy the dbus-serialbattery-{version} folder from the archive to `/data/etc/` and rename it to `dbus-serialbattery`
   - copy or move rc.local to `/data/`
   - copy or move serial-starter.d to `/data/conf/`
   - change permissions to allow execute (rwxr-xr-x) to 
      - /data/rc.local 
      - /data/etc/dbus-serialbattery/dbus-serialbattery.py
      - /data/etc/dbus-serialbattery/service/log/run
      - /data/etc/dbus-serialbattery/service/run
   - reboot your VenusOS device and check if your battery is connected

### Troubleshoot
Look for a log file under /data/log/dbus-serialbattery.ttyUSB0/current where ttyUSB0 will be your USB port (ttyUSB0/ttyUSB1/ttyUSB2/etc.)
The log file will tell you what the driver did and where it failed.
If you do not find a log folder under /data/log/dbus-serialbattery* then check
   - Do you have all the files and folders as in the downloaded archive?
   - Do the files have the execute permissions?
   - Have you moved the 2 files to their locations?
   - Look at the logfile at /data/log/serial-starter/current to see if the serial-starter service found any error starting the serialbattery driver.

### Forum help
Forum thead for this driver can be [found here](https://energytalk.co.za/t/diy-serial-battery-driver-for-victron-gx/80)
