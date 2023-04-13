import QtQuick 1.1
import "utils.js" as Utils

MbPage {
	id: root
	property string bindPrefix

	model: VisibleItemModel {
		MbItemOptions {
			id: systemSwitch
			description: qsTr("System Switch")
			bind: Utils.path(bindPrefix, "/SystemSwitch")
			readonly: true
			possibleValues:[
				MbOption{description: qsTr("Disabled"); value: 0},
				MbOption{description: qsTr("Enabled"); value: 1}
			]
		}

		MbItemOptions {
			description: qsTr("Allow to charge")
			bind: Utils.path(bindPrefix, "/Io/AllowToCharge")
			readonly: true
			possibleValues:[
				MbOption{description: qsTr("No"); value: 0},
				MbOption{description: qsTr("Yes"); value: 1}
			]
		}

		MbItemOptions {
			description: qsTr("Allow to discharge")
			bind: Utils.path(bindPrefix, "/Io/AllowToDischarge")
			readonly: true
			possibleValues:[
				MbOption{description: qsTr("No"); value: 0},
				MbOption{description: qsTr("Yes"); value: 1}
			]
		}

		MbItemOptions {
			description: qsTr("Allow to balance")
			bind: service.path("/Io/AllowToBalance")
			readonly: true
			show: item.valid
			possibleValues:[
				MbOption{description: qsTr("No"); value: 0},
				MbOption{description: qsTr("Yes"); value: 1}
			]
		}

		MbItemOptions {
			description: qsTr("External relay")
			bind: Utils.path(bindPrefix, "/Io/ExternalRelay")
			readonly: true
			show: item.valid
			possibleValues:[
				MbOption{description: qsTr("Inactive"); value: 0},
				MbOption{description: qsTr("Active"); value: 1}
			]
		}

		MbItemOptions {
			description: qsTr("Programmable Contact")
			bind: Utils.path(bindPrefix, "/Io/ProgrammableContact")
			readonly: true
			show: item.valid
			possibleValues:[
				MbOption{description: qsTr("Inactive"); value: 0},
				MbOption{description: qsTr("Active"); value: 1}
			]
		}
	}
}
