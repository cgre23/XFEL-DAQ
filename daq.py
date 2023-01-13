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


class DAQApp(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        # Initialize parameters
        self.daterange = 0
        self.ui = Ui_Form()
        self.ui.setupUi(self)
           





    def choose_output_directory(self):  # self.parent.data_dir
        self.folderpath = QtWidgets.QFileDialog.getExistingDirectory(
            self, caption='Choose Directory', directory=os.getcwd())
        if self.folderpath != []:
            print(self.folderpath)
            self.ui.filenameEdit.setText(self.folderpath)
            self.outpath = self.folderpath
            self.ui.pushButton.setEnabled(True)
            # Do Action
        else:
            self.ui.status_text.setText('No output directory selected')


    def open_file_catalogue(self):  # self.parent.data_dir
        self.streampath_cat, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Pick channel description file", "/daq/xfel/admtemp", 'xml (*.xml)', None, QtWidgets.QFileDialog.DontUseNativeDialog)
        if self.streampath_cat != "":
            filename_cat = os.path.basename(self.streampath_cat)
            self.ui.filenameEdit2.setText(filename_cat)
            self.ui.loadcataloguepb.setEnabled(
                self.check_xml_filename(self.streampath_cat))
        else:
            self.ui.filenameEdit2.setText('')

    def nested_dict(self, n, type):
        if n == 1:
            return defaultdict(type)
        else:
            return defaultdict(lambda: self.nested_dict(n-1, type))

    def search_bar(self, s):
        # Clear current selection.
        self.ui.treeWidget_2.setCurrentItem(None)
        if not s:
            # Empty string, don't search.
            return
        matching_items = self.ui.treeWidget_2.findItems(s, Qt.MatchContains)
        if matching_items:
            # We have found something.
            item = matching_items[0]  # Take the first.
            self.ui.treeWidget_2.setCurrentItem(item)

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


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = DAQApp()

    path = 'gui/xfel.png'
    app.setWindowIcon(QtGui.QIcon(path))
    window.show()
    window.raise_()

    sys.exit(app.exec_())
