import QtQuick 1.1
import com.victron.velib 1.0
import "utils.js" as Utils

MbPage {
	id: root
	property string bindPrefix: "com.victronenergy.settings//Settings/Devices/serialbattery/"

	property VBusItem cellVoltageMin: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/CellVoltageMin")}
	property VBusItem cellVoltageMax: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/CellVoltageMax")}
	property VBusItem cellVoltageFloat: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/CellVoltageFloat")}
	property VBusItem voltageMaxTime: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/VoltageMaxTime")}
	property VBusItem voltageResetSocLimit: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/VoltageResetSocLimit")}
	property VBusItem maxCurrentCharge: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/MaxCurrentCharge")}
	property VBusItem maxCurrentDischarge: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/MaxCurrentDischarge")}
	property VBusItem allowDynamicChargeCurrent: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/AllowDynamicChargeCurrent")}
	property VBusItem allowDynamicDischargeCurrent: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/AllowDynamicDischargeCurrent")}
	property VBusItem allowDynamicChargeVoltage: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/AllowDynamicChargeVoltage")}
	property VBusItem socLowWarning: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/SocLowWarning")}
	property VBusItem socLowAlarm: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/SocLowAlarm")}
	property VBusItem capacity: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/Capacity")}
	property VBusItem enableInvertedCurrent: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/EnableInvertedCurrent")}

	property VBusItem ccmSocLimitCharge1: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/CCMSocLimitCharge1")}
	property VBusItem ccmSocLimitCharge2: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/CCMSocLimitCharge2")}
	property VBusItem ccmSocLimitCharge3: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/CCMSocLimitCharge3")}
	property VBusItem ccmSocLimitDischarge1: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/CCMSocLimitDischarge1")}
	property VBusItem ccmSocLimitDischarge2: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/CCMSocLimitDischarge2")}
	property VBusItem ccmSocLimitDischarge3: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/CCMSocLimitDischarge3")}
	property VBusItem ccmCurrentLimitCharge1: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/CCMCurrentLimitCharge1")}
	property VBusItem ccmCurrentLimitCharge2: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/CCMCurrentLimitCharge2")}
	property VBusItem ccmCurrentLimitCharge3: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/CCMCurrentLimitCharge3")}
	property VBusItem ccmCurrentLimitDischarge1: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/CCMCurrentLimitDischarge1")}
	property VBusItem ccmCurrentLimitDischarge2: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/CCMCurrentLimitDischarge2")}
	property VBusItem ccmCurrentLimitDischarge3: VBusItem {bind: Utils.path("com.victronenergy.settings", "/Settings/Devices/serialbattery/CCMCurrentLimitDischarge3")}
	
	title: service.description + " | Cell Voltages"

	model: VisualItemModel {

		MbSpinBox {
			description: qsTr("Maximum charge current")
			item {
				bind: maxCurrentCharge.bind
				unit: "A"
				decimals: 0
				step: 1
				min: 0
			}
		}
		MbSpinBox {
			description: qsTr("Maximum discharge current")
			item {
				bind: maxCurrentDischarge.bind
				unit: "A"
				decimals: 0
				step: 1
				min: 0
			}
		}

		MbSpinBox {
			description: qsTr("Maximum cell voltage")
			item {
				bind: cellVoltageMax.bind
				unit: "V"
				decimals: 2
				step: 0.05
			}
		}
		MbSpinBox {
			description: qsTr("Minimum cell voltage")
			item {
				bind: cellVoltageMin.bind
				unit: "V"
				decimals: 2
				step: 0.05
			}
		}
	
		MbSwitch {
			id: allowDynamicChargeCurrentSwitch
			name: qsTr("Dynamic charge current")
			bind: allowDynamicChargeCurrent.bind
		}
		MbSwitch {
			id: allowDynamicDischargeCurrentSwitch
			name: qsTr("Dynamic discharge current")
			bind: allowDynamicDischargeCurrent.bind
		}

		MbSwitch {
			id: allowDynamicChargeVoltageSwitch
			name: qsTr("Dynamic charge voltage")
			bind : allowDynamicChargeVoltage.bind
		}

		MbSpinBox {
			description: qsTr("Float cell voltage")
			item {
				bind: cellVoltageFloat.bind
				unit: "V"
				decimals: 2
				step: 0.05
			}
			show: allowDynamicChargeVoltageSwitch.checked
		}

		MbSpinBox {
			description: qsTr("Low SOC Warning")
			item {
				bind: socLowWarning.bind
				unit: "%"
				decimals: 0
				step: 1
			}
		}
		MbSpinBox {
			description: qsTr("Low SOC Alarm")
			item {
				bind: socLowAlarm.bind
				unit: "%"
				decimals: 0
				step: 1
			}
		}


		
		

	}
}
