import sys
import string
import os
import numpy as np
import pandas as pd
from os import listdir
from os.path import isfile, join
import h5py
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QApplication, QFileDialog
from gui.UIdaq import Ui_Form
import shutil
import re
from datetime import datetime
from functools import reduce
import pyarrow as pa
import pyarrow.parquet as pq
from collections import defaultdict
from modules.spectr_gui import send_to_desy_elog
import pydoocs


class DAQApp(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        # Initialize parameters
        self.daterange = 0
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.logstring = []
        self.sa1_sequence_address = 'XFEL.UTIL/TASKOMAT/SASE2LinkColors'
           
        self.xml_name_matches = ["main", "run", "chan", "dscr", ".xml"]
        self.ui.browsepb.clicked.connect(self.open_file_catalogue)
        self.ui.sequence_button.setCheckable(True)
        self.ui.sequence_button.clicked.connect(self.toggleButton)

                

    def toggleButton(self):
        # if button is checked
        if self.ui.sequence_button.isChecked():
            # setting background color to blue
            self.palette = self.ui.sequence_button.palette()
            self.palette.setColor(QtGui.QPalette.Button, QtGui.QColor('blue'))
            self.ui.sequence_button.setPalette(self.palette)
            self.ui.sequence_button.setText("Stop SASE 1 DAQ")
            self.start_sa1_sequence()
        # if it is unchecked
        else:
            # set background color back to white
            self.palette = self.ui.sequence_button.palette()
            self.palette.setColor(QtGui.QPalette.Button, QtGui.QColor('white'))
            self.ui.sequence_button.setPalette(self.palette)
            self.ui.sequence_button.setText("Start SASE 1 DAQ")

    def start_sa1_sequence(self):
        pydoocs.write(self.sa1_sequence_address+'/RUN.ONCE', 1)


        self.last_log = pydoocs.read(self.sa1_sequence_address+'/LOG_HTML.LAST')['data']
        self.logstring.append(self.last_log)
        self.ui.textBrowser.append(self.last_log)
        

         
        #self.logbook_entry(widget=self.tab, text=self.logstring)


    

    def open_file_catalogue(self):  # self.parent.data_dir
        self.streampath_cat, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Pick channel description file", "/daq/xfel/admtemp", 'xml (*.xml)', None, QtWidgets.QFileDialog.DontUseNativeDialog)
        if self.streampath_cat != "":
            filename_cat = os.path.basename(self.streampath_cat)
            self.ui.filenameEdit.setText(filename_cat)
            #self.ui.loadcataloguepb.setEnabled(
            #    self.check_xml_filename(self.streampath_cat))
        else:
            self.ui.filenameEdit.setText('')

    def nested_dict(self, n, type):
        if n == 1:
            return defaultdict(type)
        else:
            return defaultdict(lambda: self.nested_dict(n-1, type))

    def check_xml_filename(self, path):
        if all(x in path for x in self.xml_name_matches):
            return True
        else:
            return False

    def makedirs(self, dest):
        if not os.path.exists(dest):
            os.makedirs(dest)

    def deletedirs(self):
        path = os.getcwd()
        file_path = path + '/temp/'
        try:
            shutil.rmtree(file_path)
            print("Temp file deleted.")
        except OSError as e:
            print("Error: %s : %s" % (file_path, e.strerror))

    def error_box(self, message):
        QtGui.QMessageBox.about(self, "Error box", message)

    def question_box(self, message):
        #QtGui.QMessageBox.question(self, "Question box", message)
        reply = QtGui.QMessageBox.question(self, "Question Box",
                                           message,
                                           QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            return True

        return False

    def logbook_entry(self, widget, text=""):
        """
        Method to send data + screenshot to eLogbook
        :return:
        """
        #screenshot = self.get_screenshot(widget)
        res = send_to_desy_elog(
            author="", title="SA1 DAQ Sequence", severity="INFO", text=text, elog="xfellog")
        if res == True:
            self.ui.textBrowser.append('Finished scan! Logbook entry submitted.')
        if not res:
            self.ui.textBrowser.append('Finished scan! Error during eLogBook sending.')

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = DAQApp()

    path = 'gui/xfel.png'
    app.setWindowIcon(QtGui.QIcon(path))
    window.show()
    window.raise_()

    sys.exit(app.exec_())
