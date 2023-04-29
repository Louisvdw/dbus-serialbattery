---
id: supported-bms
title: Supported BMS
sidebar_position: 3
# Display h2 to h4 headings
toc_min_heading_level: 2
toc_max_heading_level: 4
---

# Supported BMS

## Currently supported
### &bull; ANT BMS
Disabled by default since driver version `v1.0.0` as it causes other issues. More informations can be found in [Add other use case (grid meter) or ignore devices - ANT BMS check missing](https://github.com/Louisvdw/dbus-serialbattery/issues/479) and if it was fixed. See [How to enable a disabled BMS](../general/install#how-to-enable-a-disabled-bms) to enable the BMS.

### &bull; Daly Smart BMS
Including:
#### - Sinowealth based Daly BMS
Disabled by default since driver version `v0.14.0` as it causes other issues. See [How to enable a disabled BMS](../general/install#how-to-enable-a-disabled-bms) to enable the BMS.

![Daly app](../../screenshots/bms-daly.jpg)

### &bull; ECS GreenMeter with LiPro

### &bull; HLPdataBMS4S

### &bull; [JKBMS](https://www.jkbms.com/products/) / Heltec BMS

### &bull; Life/Tian Power
Including:

#### - Revov

### &bull; MNB spi BMS
Disabled by default as it requires additional manual steps to install.

### &bull; Renogy BMS

### &bull; Seplos
So far only tested on version `16E`.

### &bull; Smart BMS
Including:
#### - [LLT Power](https://www.lithiumbatterypcb.com/product-instructionev-battery-pcb-boardev-battery-pcb-board/ev-battery-pcb-board/smart-bms-of-power-battery/)
#### - [Jiabaida JDB BMS](https://dgjbd.en.alibaba.com/)
#### - Overkill Solar
#### - Other BMS that use the Xiaoxiang phone app

| Android | iOS |
|-|-|
| ![Xiaoxian app](../../screenshots/bms-xiaoxian-android.jpg) | ![Xiaoxian app](../../screenshots/bms-xiaoxian-ios.jpg) |

## Planned support

You can view the current [BMS requests](https://github.com/Louisvdw/dbus-serialbattery/discussions/categories/new-bms-requests) to see which BMS support is requested and vote for the BMS you want to be supported.

## Add/Request new BMS
There are two possibilities to add a new BMS.

1. Fork the repository and use the [`battery_template.py`](https://github.com/mr-manuel/venus-os_dbus-serialbattery/blob/master/etc/dbus-serialbattery/bms/battery_template.py) as template to add a new battery. As soon as the BMS works you can open a PR (pull request) to merge it.

2. Start a [new discussion](https://github.com/Louisvdw/dbus-serialbattery/discussions/new?category=new-bms-requests) in the `New BMS request` category. Please add also the protocol documentation which you can request from the manufacturer/seller. The more upvotes the BMS request has, the higher is the priority.

If you would like to donate hardware or would like to help testing a specific BMS please get in contact over the [discussions section](https://github.com/Louisvdw/dbus-serialbattery/discussions).


## Which BMS are you using?
Please let us know, which BMS you are using with the driver by upvoting your BMS: [Which BMS are you using?](https://github.com/Louisvdw/dbus-serialbattery/discussions/546)
