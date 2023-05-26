---
id: index
title: Introduction
slug: /
sidebar_position: 1
---

# dbus-serialbattery
This is a driver for Venus OS devices (any GX device sold by Victron or a Raspberry Pi running the Venus OS image).

The driver will communicate with a Battery Management System (BMS) that support serial (RS232, RS485 or TTL UART) and Bluetooth communication (see [BMS feature comparison](https://louisvdw.github.io/dbus-serialbattery/general/features#bms-feature-comparison) for details). The data is then published to the Venus OS system (dbus). The main purpose is to act as a Battery Monitor in your GX and supply State of Charge (SoC) and other values to the inverter/charger.

### Supporting this project
If you find this driver helpful please consider supporting this project. You can buy me a Ko-Fi or get in contact, if you would like to donate hardware for development.

### Support [Louisvdw](https://github.com/Louisvdw)
* Main developer
* Added most of the BMS drivers

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/Z8Z73LCW1) or using [Paypal.me](https://paypal.me/innernet)

### Support [mr-manuel](https://github.com/mr-manuel)
* Added a lot of features, optimizations and improvements with `v1.0.x`
* Added a lot of documentation to the config file and notes that are displayed after installation for better understanding
* Introduced the new documentation page of the driver and reworked a great part of it for easier understanding

[<img src="https://github.md0.eu/uploads/donate-button.svg" width="178" />](https://www.paypal.com/donate/?hosted_button_id=3NEVZBDM5KABW)

## Requirements

* GX device or Raspberry Pi running Venus OS version `v2.80` or later.

## Screenshots

### Venus OS

![VenusOS](../../screenshots/venus-os_001.png)
![VenusOS](../../screenshots/venus-os_002.png)
![VenusOS](../../screenshots/venus-os_003.png)
![VenusOS](../../screenshots/venus-os_004.png)
![VenusOS](../../screenshots/venus-os_005.png)
![VenusOS](../../screenshots/venus-os_006.png)
![VenusOS](../../screenshots/venus-os_007.png)
![VenusOS](../../screenshots/venus-os_008.png)
![VenusOS](../../screenshots/venus-os_009.png)
![VenusOS](../../screenshots/venus-os_010.png)
![VenusOS](../../screenshots/venus-os_011.png)
![VenusOS](../../screenshots/venus-os_012.png)
![VenusOS](../../screenshots/venus-os_013.png)

### VRM Portal

![VenusOS](../../screenshots/vrm-portal_001.png)
![VenusOS](../../screenshots/vrm-portal_002.png)
![VenusOS](../../screenshots/vrm-portal_003.png)
![VenusOS](../../screenshots/vrm-portal_004.png)
![VenusOS](../../screenshots/vrm-portal_005.png)
![VenusOS](../../screenshots/vrm-portal_006.png)
![VenusOS](../../screenshots/vrm-portal_007.png)
![VenusOS](../../screenshots/vrm-portal_008.png)
![VenusOS](../../screenshots/vrm-portal_009.png)
