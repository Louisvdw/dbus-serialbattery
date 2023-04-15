---
id: features
title: Features
---

## Features
The driver will act as Battery Monitor inside VenusOS and update the following values:
* State Of Charge
* Voltage
* Current
* Power
* Can handle batteries with from 3 - 32 cells
* battery temperature
* min/max cell voltages
* raise alarms from the BMS
* available capacity
* remaining capacity
* total Ah drawn
* history of charge cycles
* Charge current control management (CCCM)
* set battery parameters (DVCC)
    - Charge Voltage Limit(CVL)
    - Charge Current Limit(CCL)
    - Discharge Current Limit(DCL)
    - CVL (Battery Max) automatically adjusted by cell count * 3.45V
    - Battery Min automatically adjusted by cell count * 3.1V
![VenusOS values](https://raw.githubusercontent.com/Louisvdw/dbus-serialbattery/master/images/GXvalues.png)


## Charge current control management
CCCM limits the current when the battery is close to full or close to empty.
When your battery is full, the reduced charge current will give the balancers in your BMS time to work
When your battery is close to empty the reduced dicharge current will limit that a sudden large load will pull your battery cells below their protection values.

### Limitation Modes
The limits can be applied in Step or Linear mode.
Step use hard boundaries that will apply recognisable step values and use less processing power (DEFAULT)
Linear will give a gradual change from one limit range to the next.

### CCCM attributes
You can set CCCM limits for 3 attributes which can be Enabled/Disabled and adjusted by settings in utils.py
The smallest limit from all enabled will apply.

### SOC (State Of Charge) from the BMS
* CCCM_SOC_ENABLE = True/False
* DCCM_SOC_ENABLE = True/False

  CCCM limits the charge/discharge current depending on the SOC

    - between 99% - 100% => 5A charge
    - between 95% - 98% => 1/4 Max charge
    - between 91% - 95% => 1/2 Max charge

    - 30% - 91% => Max charge and Max discharge

    - between 20% - 30% => 1/2 Max discharge
    - between 10% - 20% => 1/4 Max discharge
    - below <= 10% => 5A

### Cell Voltage
* CCCM_CV_ENABLE = True/False
* DCCM_CV_ENABLE = True/False

  CCCM limits the charge/discharge current depending on the highest/lowest cell voltages

    - between 3.50V - 3.55V => 2A charge
    - between 3.45V - 3.50V => 30A charge
    - between 3.30V - 3.45V => 60A

    - 3.30V - 3.10V => Max charge and Max discharge (60A)

    - between 2.90V - 3.10V => 30A discharge
    - between 2.8V - 2.9V => 5A discharge
    - below <= 2.70V => 0A discharge

### Temprature
* CCCM_T_ENABLE = True/False
* DCCM_T_ENABLE = True/False

  CCCM limits the charge/discharge current depending on the highest/lowest temperature sensor values
  Charging will be 0A if below 0°C or above 55°C
  Discharging will be 0A if below -20°C or above 55°C

![VenusOS values](https://raw.githubusercontent.com/Louisvdw/dbus-serialbattery/master/images/VRMChargeLimits.png)

## Charge voltage control management
### Cell voltage penalty
### Float voltage emulation

## Battery feature comparison
| Feature | JBD/LLT | Daly | ANT | MNB | JKBMS | RENOGY | TIAN/LIFE Power | ECS |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| State Of Charge | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Voltage | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Current | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Power | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| battery temperature | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| min/max cell voltages | Yes | Yes | Yes | Yes | Yes | Yes | Yes | No |
| raise alarms from the BMS | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes(no Cells yet) |
| available capacity | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| remaining capacity | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| total Ah drawn | Calc | Calc | Yes | Calc | Calc | Calc | Calc | Calc |
| history of charge cycles | Yes | Yes | Yes | Yes | Yes | Yes | Yes | No |
| set battery parameters | Fixed | Fixed | Fixed | Fixed | Fixed | Fixed | Fixed | Yes |
| Charge current control | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
