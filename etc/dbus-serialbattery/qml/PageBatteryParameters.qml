import QtQuick 1.1
import com.victron.velib 1.0

MbPage {
	id: root

	property variant service

	model: VisibleItemModel {

        MbItemValue {
            description: qsTr("Charge Mode")
            item.bind: service.path("/Info/ChargeMode")
            show: item.valid
        }

		MbItemValue {
			description: qsTr("Charge Voltage Limit (CVL)")
			item.bind: service.path("/Info/MaxChargeVoltage")
		}

        MbItemValue {
            description: qsTr("Charge Limitation")
            item.bind: service.path("/Info/ChargeLimitation")
            show: item.valid
        }

		MbItemValue {
			description: qsTr("Charge Current Limit (CCL)")
			item.bind: service.path("/Info/MaxChargeCurrent")
		}

        MbItemValue {
            description: qsTr("Discharge Limitation")
            item.bind: service.path("/Info/DischargeLimitation")
            show: item.valid
        }

		MbItemValue {
			description: qsTr("Discharge Current Limit (DCL)")
			item.bind: service.path("/Info/MaxDischargeCurrent")
		}

		MbItemValue {
			description: qsTr("Low Voltage Disconnect (always ignored)")
			item.bind: service.path("/Info/BatteryLowVoltage")
			showAccessLevel: User.AccessService
		}
	}
}
