import QtQuick 1.1
import com.victron.velib 1.0
import "utils.js" as Utils

MbPage {
        id: root
        property string bindPrefix

        model: VisibleItemModel {
                MbSubMenu {
                        id: battery
                        description: qsTr("Battery bank")
                        subpage: Component {
                                PageBatterySettingsBattery {
                                        title: battery.description
                                        bindPrefix: root.bindPrefix
                                }
                        }
                }

                MbSubMenu {
                        id: alarms
                        description: qsTr("Alarms")
                        subpage: Component {
                                PageBatterySettingsAlarm {
                                        title: alarms.description
                                        bindPrefix: root.bindPrefix
                                }
                        }
                }

                MbSubMenu {
                        id: relay
                        description: qsTr("Relay (on battery monitor)")
                        subpage: Component {
                                PageBatterySettingsRelay {
                                        title: relay.description
                                        bindPrefix: root.bindPrefix
                                }
                        }
                }

                MbItemOptions {
                        description: qsTr("Restore factory defaults")
                        bind: Utils.path(root.bindPrefix, "/Settings/RestoreDefaults")
                        text: qsTr("Press to restore")
                        show: valid
                        possibleValues: [
                                MbOption { description: qsTr("Cancel"); value: 0 },
                                MbOption { description: qsTr("Restore"); value: 1 }
                        ]
                }

                MbItemNoYes {
                        description: qsTr("Bluetooth Enabled")
                        bind: Utils.path(bindPrefix, "/Settings/BluetoothMode")
                        show: valid
                }

        
                MbSpinBox {
                        description: "Reset SoC to"
                        item.bind: Utils.path(bindPrefix, "/Settings/ResetSoc")
                        item.min: 0
                        item.max: 100
                        item.step: 1
                }




        }
}
