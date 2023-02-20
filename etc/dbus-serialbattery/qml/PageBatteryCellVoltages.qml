import QtQuick 1.1
import com.victron.velib 1.0

MbPage {
    id: root
    property string bindPrefix
    property VBusItem _b1: VBusItem { bind: service.path("/Balances/Cell1") }
    property VBusItem _b2: VBusItem { bind: service.path("/Balances/Cell2") }
    property VBusItem _b3: VBusItem { bind: service.path("/Balances/Cell3") }
    property VBusItem _b4: VBusItem { bind: service.path("/Balances/Cell4") }
    property VBusItem _b5: VBusItem { bind: service.path("/Balances/Cell5") }
    property VBusItem _b6: VBusItem { bind: service.path("/Balances/Cell6") }
    property VBusItem _b7: VBusItem { bind: service.path("/Balances/Cell7") }
    property VBusItem _b8: VBusItem { bind: service.path("/Balances/Cell8") }
    property VBusItem _b9: VBusItem { bind: service.path("/Balances/Cell9") }
    property VBusItem _b10: VBusItem { bind: service.path("/Balances/Cell10") }
    property VBusItem _b11: VBusItem { bind: service.path("/Balances/Cell11") }
    property VBusItem _b12: VBusItem { bind: service.path("/Balances/Cell12") }
    property VBusItem _b13: VBusItem { bind: service.path("/Balances/Cell13") }
    property VBusItem _b14: VBusItem { bind: service.path("/Balances/Cell14") }
    property VBusItem _b15: VBusItem { bind: service.path("/Balances/Cell15") }
    property VBusItem _b16: VBusItem { bind: service.path("/Balances/Cell16") }
    property VBusItem _b17: VBusItem { bind: service.path("/Balances/Cell17") }
    property VBusItem _b18: VBusItem { bind: service.path("/Balances/Cell18") }
    property VBusItem _b19: VBusItem { bind: service.path("/Balances/Cell19") }
    property VBusItem _b20: VBusItem { bind: service.path("/Balances/Cell20") }
    property VBusItem _b21: VBusItem { bind: service.path("/Balances/Cell21") }
    property VBusItem _b22: VBusItem { bind: service.path("/Balances/Cell22") }
    property VBusItem _b23: VBusItem { bind: service.path("/Balances/Cell23") }
    property VBusItem _b24: VBusItem { bind: service.path("/Balances/Cell24") }
    property VBusItem volt1: VBusItem { bind: service.path("/Voltages/Cell1") }
    property VBusItem volt2: VBusItem { bind: service.path("/Voltages/Cell2") }
    property VBusItem volt3: VBusItem { bind: service.path("/Voltages/Cell3") }
    property VBusItem volt4: VBusItem { bind: service.path("/Voltages/Cell4") }
    property VBusItem volt5: VBusItem { bind: service.path("/Voltages/Cell5") }
    property VBusItem volt6: VBusItem { bind: service.path("/Voltages/Cell6") }
    property VBusItem volt7: VBusItem { bind: service.path("/Voltages/Cell7") }
    property VBusItem volt8: VBusItem { bind: service.path("/Voltages/Cell8") }
    property VBusItem volt9: VBusItem { bind: service.path("/Voltages/Cell9") }
    property VBusItem volt10: VBusItem { bind: service.path("/Voltages/Cell10") }
    property VBusItem volt11: VBusItem { bind: service.path("/Voltages/Cell11") }
    property VBusItem volt12: VBusItem { bind: service.path("/Voltages/Cell12") }
    property VBusItem volt13: VBusItem { bind: service.path("/Voltages/Cell13") }
    property VBusItem volt14: VBusItem { bind: service.path("/Voltages/Cell14") }
    property VBusItem volt15: VBusItem { bind: service.path("/Voltages/Cell15") }
    property VBusItem volt16: VBusItem { bind: service.path("/Voltages/Cell16") }
    property VBusItem volt17: VBusItem { bind: service.path("/Voltages/Cell17") }
    property VBusItem volt18: VBusItem { bind: service.path("/Voltages/Cell18") }
    property VBusItem volt19: VBusItem { bind: service.path("/Voltages/Cell19") }
    property VBusItem volt20: VBusItem { bind: service.path("/Voltages/Cell20") }
    property VBusItem volt21: VBusItem { bind: service.path("/Voltages/Cell21") }
    property VBusItem volt22: VBusItem { bind: service.path("/Voltages/Cell22") }
    property VBusItem volt23: VBusItem { bind: service.path("/Voltages/Cell23") }
    property VBusItem volt24: VBusItem { bind: service.path("/Voltages/Cell24") }
    property string c1: _b1.valid && _b1.text == "1" ? "#ff0000" : "#ddd"
    property string c2: _b2.valid && _b2.text == "1" ? "#ff0000" : "#ddd"
    property string c3: _b3.valid && _b3.text == "1" ? "#ff0000" : "#ddd"
    property string c4: _b4.valid && _b4.text == "1" ? "#ff0000" : "#ddd"
    property string c5: _b5.valid && _b5.text == "1" ? "#ff0000" : "#ddd"
    property string c6: _b6.valid && _b6.text == "1" ? "#ff0000" : "#ddd"
    property string c7: _b7.valid && _b7.text == "1" ? "#ff0000" : "#ddd"
    property string c8: _b8.valid && _b8.text == "1" ? "#ff0000" : "#ddd"
    property string c9: _b9.valid && _b9.text == "1" ? "#ff0000" : "#ddd"
    property string c10: _b10.valid && _b10.text == "1" ? "#ff0000" : "#ddd"
    property string c11: _b11.valid && _b11.text == "1" ? "#ff0000" : "#ddd"
    property string c12: _b12.valid && _b12.text == "1" ? "#ff0000" : "#ddd"
    property string c13: _b13.valid && _b13.text == "1" ? "#ff0000" : "#ddd"
    property string c14: _b14.valid && _b14.text == "1" ? "#ff0000" : "#ddd"
    property string c15: _b15.valid && _b15.text == "1" ? "#ff0000" : "#ddd"
    property string c16: _b16.valid && _b16.text == "1" ? "#ff0000" : "#ddd"
    property string c17: _b17.valid && _b17.text == "1" ? "#ff0000" : "#ddd"
    property string c18: _b18.valid && _b18.text == "1" ? "#ff0000" : "#ddd"
    property string c19: _b19.valid && _b19.text == "1" ? "#ff0000" : "#ddd"
    property string c20: _b20.valid && _b20.text == "1" ? "#ff0000" : "#ddd"
    property string c21: _b21.valid && _b21.text == "1" ? "#ff0000" : "#ddd"
    property string c22: _b22.valid && _b22.text == "1" ? "#ff0000" : "#ddd"
    property string c23: _b23.valid && _b23.text == "1" ? "#ff0000" : "#ddd"
    property string c24: _b24.valid && _b24.text == "1" ? "#ff0000" : "#ddd"
    title: service.description + " | Cell Voltages"

    model: VisibleItemModel {

        MbItemRow {
            description: qsTr("Cells Sum")
            values: [
                MbTextBlock { item { bind: service.path("/Voltages/Sum") } width: 70; height: 25 }
            ]
        }
        MbItemRow {
            description: qsTr("Cells (Min/Max/Diff)")
            values: [
                MbTextBlock { item { bind: service.path("/System/MinCellVoltage") } width: 70; height: 25 },
                MbTextBlock { item { bind: service.path("/System/MaxCellVoltage") } width: 70; height: 25 },
                MbTextBlock { item { bind: service.path("/Voltages/Diff") } width: 70; height: 25 }
            ]
        }
        MbItemRow {
            description: qsTr("Cells (1/2/3/4)")
            height: 22
            values: [
                MbTextBlock { item: volt1; width: 70; height: 20; color: c1 },
                MbTextBlock { item: volt2; width: 70; height: 20; color: c2 },
                MbTextBlock { item: volt3; width: 70; height: 20; color: c3 },
                MbTextBlock { item: volt4; width: 70; height: 20; color: c4 }
            ]
        }
        MbItemRow {
            description: qsTr("Cells (5/6/7/8)")
            height: 22
            show: volt5.valid
            values: [
                MbTextBlock { item: volt5; width: 70; height: 20; color: c5 },
                MbTextBlock { item: volt6; width: 70; height: 20; color: c6 },
                MbTextBlock { item: volt7; width: 70; height: 20; color: c7 },
                MbTextBlock { item: volt8; width: 70; height: 20; color: c8 }
            ]
        }
        MbItemRow {
            description: qsTr("Cells (9/10/11/12)")
            height: 22
            show: volt9.valid
            values: [
                MbTextBlock { item: volt9; width: 70; height: 20; color: c9 },
                MbTextBlock { item: volt10; width: 70; height: 20; color: c10 },
                MbTextBlock { item: volt11; width: 70; height: 20; color: c11 },
                MbTextBlock { item: volt12; width: 70; height: 20; color: c12 }
            ]
        }
        MbItemRow {
            description: qsTr("Cells (13/14/15/16)")
            height: 22
            show: volt13.valid
            values: [
                MbTextBlock { item: volt13; width: 70; height: 20; color: c13 },
                MbTextBlock { item: volt14; width: 70; height: 20; color: c14 },
                MbTextBlock { item: volt15; width: 70; height: 20; color: c15 },
                MbTextBlock { item: volt16; width: 70; height: 20; color: c16 }
            ]
        }
        MbItemRow {
            description: qsTr("Cells (17/18/19/20)")
            height: 22
            show: volt17.valid
            values: [
                MbTextBlock { item: volt17; width: 70; height: 20; color: c13 },
                MbTextBlock { item: volt18; width: 70; height: 20; color: c14 },
                MbTextBlock { item: volt19; width: 70; height: 20; color: c15 },
                MbTextBlock { item: volt20; width: 70; height: 20; color: c16 }
            ]
        }
        MbItemRow {
            description: qsTr("Cells (21/22/23/24)")
            height: 22
            show: volt21.valid
            values: [
                MbTextBlock { item: volt21; width: 70; height: 20; color: c13 },
                MbTextBlock { item: volt22; width: 70; height: 20; color: c14 },
                MbTextBlock { item: volt23; width: 70; height: 20; color: c15 },
                MbTextBlock { item: volt24; width: 70; height: 20; color: c16 }
            ]
        }
    }
}
