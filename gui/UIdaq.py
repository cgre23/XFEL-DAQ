# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UIDAQ.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.setEnabled(True)
        Form.resize(633, 698)
        Form.setMinimumSize(QtCore.QSize(0, 0))
        Form.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        Form.setWindowOpacity(1.0)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtWidgets.QTabWidget(Form)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.tab)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.groupBox = QtWidgets.QGroupBox(self.tab)
        self.groupBox.setObjectName("groupBox")
        self.sequence_button = QtWidgets.QPushButton(self.groupBox)
        self.sequence_button.setGeometry(QtCore.QRect(90, 220, 399, 32))
        self.sequence_button.setObjectName("sequence_button")
        self.convert_button = QtWidgets.QPushButton(self.groupBox)
        self.convert_button.setGeometry(QtCore.QRect(90, 320, 399, 32))
        self.convert_button.setObjectName("convert_button")
        self.gridLayout_3.addWidget(self.groupBox, 3, 0, 1, 1)
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.tab_2)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.groupBox_2 = QtWidgets.QGroupBox(self.tab_2)
        self.groupBox_2.setObjectName("groupBox_2")
        self.label_3 = QtWidgets.QLabel(self.groupBox_2)
        self.label_3.setGeometry(QtCore.QRect(20, 50, 200, 24))
        self.label_3.setMaximumSize(QtCore.QSize(200, 16777215))
        self.label_3.setObjectName("label_3")
        self.filenameEdit = QtWidgets.QLineEdit(self.groupBox_2)
        self.filenameEdit.setGeometry(QtCore.QRect(20, 80, 300, 21))
        self.filenameEdit.setMaximumSize(QtCore.QSize(300, 16777215))
        self.filenameEdit.setObjectName("filenameEdit")
        self.browsepb = QtWidgets.QPushButton(self.groupBox_2)
        self.browsepb.setGeometry(QtCore.QRect(340, 70, 100, 32))
        self.browsepb.setMaximumSize(QtCore.QSize(100, 16777215))
        self.browsepb.setObjectName("browsepb")
        self.radioButton = QtWidgets.QRadioButton(self.groupBox_2)
        self.radioButton.setGeometry(QtCore.QRect(29, 120, 301, 20))
        self.radioButton.setObjectName("radioButton")
        self.gridLayout_2.addWidget(self.groupBox_2, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab_2, "")
        self.verticalLayout.addWidget(self.tabWidget)

        self.retranslateUi(Form)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "DAQ Tool"))
        self.groupBox.setTitle(_translate("Form", "DAQ"))
        self.sequence_button.setText(_translate("Form", "Start Sequence"))
        self.convert_button.setText(_translate("Form", "Convert data"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("Form", "DAQ"))
        self.groupBox_2.setTitle(_translate("Form", "Settings"))
        self.label_3.setText(_translate("Form", "XML description file"))
        self.browsepb.setText(_translate("Form", "Browse"))
        self.radioButton.setText(_translate("Form", "Apply bunch filtering by destination?"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("Form", "Settings"))

