import QtQuick 1.1
import com.victron.velib 1.0

MbPage {
	id: root

	property variant service

	property VBusItem chargeModeDebug: VBusItem { bind: service.path("/Info/ChargeModeDebug") }
	property VBusItem chargeModeDebugFloat: VBusItem { bind: service.path("/Info/ChargeModeDebugFloat") }
	property VBusItem chargeModeDebugBulk: VBusItem { bind: service.path("/Info/ChargeModeDebugBulk") }

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

		// show debug informations
		MbItemText {
			text: chargeModeDebug.value.split('\n').slice(0, 8).join('\n') // Display first 8 lines
			wrapMode: Text.WordWrap
			show: chargeModeDebug.value != ""
		}

		MbItemText {
			text: chargeModeDebug.value.split('\n').slice(8).join('\n') // Display remaining lines
			wrapMode: Text.WordWrap
			show: chargeModeDebug.value.split('\n').length > 8 // Show only if there are more than 8 lines
		}

		MbItemText {
			text: chargeModeDebugFloat.value
			wrapMode: Text.WordWrap
			show: chargeModeDebugFloat.value != ""
		}

		MbItemText {
			text: chargeModeDebugBulk.value
			wrapMode: Text.WordWrap
			show: chargeModeDebugBulk.value != ""
		}

	}
}
