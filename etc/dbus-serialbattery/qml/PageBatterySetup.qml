import QtQuick 1.1
import com.victron.velib 1.0
import "utils.js" as Utils

MbPage {
	id: root
	property string bindPrefix
	title: "SerialBattery Setup"

	model: VisualItemModel {

		MbSwitch {
			name: qsTr("Switch")
			bind: "com.victronenergy.settings/Settings/System/SSHLocal"
		}

		

		
	}
}
