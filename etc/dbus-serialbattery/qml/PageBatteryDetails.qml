import QtQuick 1.1
import com.victron.velib 1.0
import "utils.js" as Utils

MbPage {
	id: root

	property string bindPrefix
	property BatteryDetails details: BatteryDetails { bindPrefix: root.bindPrefix }

	model: VisualItemModel {
		MbItemRow {
			description: qsTr("Lowest cell voltage")
			values: [
				MbTextBlock { item.text: details.minVoltageCellId.text },
				MbTextBlock { item.text: details.minCellVoltage.text }
			]
		}

		MbItemRow {
			description: qsTr("Highest cell voltage")
			values: [
				MbTextBlock { item.text: details.maxVoltageCellId.text },
				MbTextBlock { item.text: details.maxCellVoltage.text }
			]
		}

		MbItemRow {
			description: qsTr("Minimum cell temperature")
			values: [
				MbTextBlock { item.text: details.minTemperatureCellId.text },
				MbTextBlock { item.text: details.minCellTemperature.text }
			]
		}

		MbItemRow {
			description: qsTr("Maximum cell temperature")
			values: [
				MbTextBlock { item.text: details.maxTemperatureCellId.text },
				MbTextBlock { item.text: details.maxCellTemperature.text }
			]
		}

		MbItemRow {
			description: qsTr("Battery modules")
			values: [
				MbTextBlock { item.text: details.modulesOnline.text },
				MbTextBlock { item.text: details.modulesOffline.text }
			]
		}

		MbItemRow {
			description: qsTr("Nr. of modules blocking charge / discharge")
			values: [
				MbTextBlock { item.text: details.nrOfModulesBlockingCharge.text },
				MbTextBlock { item.text: details.nrOfModulesBlockingDischarge.text }
			]
		}

		MbItemRow {
			description: qsTr("Installed / Available capacity")
			values: [
				MbTextBlock { item.text: details.installedCapacity.text },
				MbTextBlock { item.bind: Utils.path(bindPrefix, "/Capacity") }
			]
		}
	}
}
