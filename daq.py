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
from modules.guiLoop import guiLoop
import threading, queue
import shutil
import re
from datetime import datetime
from functools import reduce
from collections import defaultdict
from modules.spectr_gui import send_to_desy_elog
import pydoocs
import subprocess
import time

class DAQApp(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        # Initialize parameters
        self.daterange = 0
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.logstring = []
        self.conversion_success = 0
        self.sa1_sequence_prefix = 'XFEL.UTIL/TASKOMAT/DAQ_SA1'
           
        self.xml_name_matches = ["main", "run", "chan", "dscr", ".xml"]
        self.ui.browsepb.clicked.connect(self.open_file_catalogue)
        self.ui.sequence_button.setCheckable(True)
        self.ui.sequence_button.clicked.connect(self.toggleSequenceButton)
        self.conversionSettings = {'starttime': 'start', 'stoptime': 'stop', 'xmldfile': '/path', 'bunchfilter': 'all'}
        self.ui.convert_button.clicked.connect(self.toggleConvertButton)
        
        self.q = queue.Queue()


    def toggleConvertButton(self):
        # if button is checked
        if self.ui.convert_button.isChecked():
            # setting background color to blue
            self.palette = self.ui.convert_button.palette()
            self.palette.setColor(QtGui.QPalette.Button, QtGui.QColor('blue'))
            self.ui.convert_button.setPalette(self.palette)
            self.ui.convert_button.setText("Force Stop File Conversion")
            start_log = datetime.now().isoformat(' ', 'seconds')+': Started file conversion.\n'
            start_log_html = '<html> <style> p { margin:0px; } span.d { font-size:80%; color:#555555; } span.e { font-weight:bold; color:#FF0000; } span.w { color:#CCAA00; } </style> <body style="font:normal 10px Arial,monospaced; margin:0; padding:0;"> Started the file conversion.  <span class="d">(datetime)</span></body></html>'.replace('datetime', datetime.now().isoformat(' ', 'seconds'))
            self.logstring.append(start_log)
            self.ui.textBrowser.append(start_log_html)
            cmd = 'modules/hello.py'
            self.q.put(cmd)
            t = threading.Thread(target=self.convertHDF5)
            t.daemon = True
            t.start()
            
            #self.conversionRAWtoHDF5('python3 modules/hello.py')
        # if it is unchecked
        else: # Force Stop
            # set background color back to white
            self.palette = self.ui.convert_button.palette()
            self.palette.setColor(QtGui.QPalette.Button, QtGui.QColor('white'))
            self.ui.convert_button.setPalette(self.palette)
            self.ui.convert_button.setText("Convert data")
            if self.conversion_success == 1:
                stop_log = datetime.now().isoformat(' ', 'seconds')+': Converted file successfully!\n'
                stop_log_html = '<html> <style> p { margin:0px; } span.d { font-size:80%; color:#555555; } span.e { font-weight:bold; color:#FF0000; } span.w { color:#CCAA00; } </style> <body style="font:normal 10px Arial,monospaced; margin:0; padding:0;"> Converted file successfully!  <span class="d">(datetime)</span></body></html>'.replace('datetime', datetime.now().isoformat(' ', 'seconds'))
                self.logstring.append(stop_log)
                self.ui.textBrowser.append(stop_log_html)
                self.logbooktext = ''.join(self.logstring)
                self.logbook_entry(text=self.logbooktext)
                self.conversion_success = 0
            else:
                # Force Stop conversion
                self.proc1.kill()
                stop_log = datetime.now().isoformat(' ', 'seconds')+': Force stopped file conversion.\n'
                stop_log_html = '<html> <style> p { margin:0px; } span.d { font-size:80%; color:#555555; } span.e { font-weight:bold; color:#FF0000; } span.w { color:#CCAA00; } </style> <body style="font:normal 10px Arial,monospaced; margin:0; padding:0;"> Force Stopped the file conversion.  <span class="d">(datetime)</span></body></html>'.replace('datetime', datetime.now().isoformat(' ', 'seconds'))
                self.logstring.append(stop_log)
                self.ui.textBrowser.append(stop_log_html)
                # Write to logbook
                self.logbooktext = ''.join(self.logstring)
            	#self.logbook_entry(widget=self.tab, text=self.logbooktext)

    def toggleSequenceButton(self):
        # if button is checked
        if self.ui.sequence_button.isChecked():
            # setting background color to blue
            self.palette = self.ui.sequence_button.palette()
            self.palette.setColor(QtGui.QPalette.Button, QtGui.QColor('blue'))
            self.ui.sequence_button.setPalette(self.palette)
            self.ui.sequence_button.setText("Force Stop SASE 1 DAQ")
            t = threading.Thread(target=self.start_sa1_sequence)
            t.daemon = True
            t.start()
            
            self.logbooktext = ''.join(self.logstring)
            #self.logbook_entry(widget=self.tab, text=self.logbooktext)
            
        # if it is unchecked
        else: # Force Stop
            # set background color back to white
            self.palette = self.ui.sequence_button.palette()
            self.palette.setColor(QtGui.QPalette.Button, QtGui.QColor('white'))
            self.ui.sequence_button.setPalette(self.palette)
            self.ui.sequence_button.setText("Start SASE 1 DAQ")

            # Force Stop sequence
            try:
                pydoocs.write(self.sa1_sequence_prefix+'/FORCESTOP', 1)
                stop_log = datetime.now().isoformat(' ', 'seconds')+': Aborted the Taskomat sequence.\n'
                stop_log_html = '<html> <style> p { margin:0px; } span.d { font-size:80%; color:#555555; } span.e { font-weight:bold; color:#FF0000; } span.w { color:#CCAA00; } </style> <body style="font:normal 10px Arial,monospaced; margin:0; padding:0;"> Aborted the Taskomat sequence.  <span class="d">(datetime)</span></body></html>'.replace('datetime', datetime.now().isoformat(' ', 'seconds'))
                self.logstring.append(stop_log)
                self.ui.textBrowser.append(stop_log_html)
                # Write to logbook
                self.logbooktext = ''.join(self.logstring)
                #self.logbook_entry(widget=self.tab, text=self.logbooktext)
            except:
                print('Not able to stop the sequence.\n')
                stop_log_html = '<html> <style> p { margin:0px; } span.d { font-size:80%; color:#555555; } span.e { font-weight:bold; color:#FF0000; } span.w { color:#CCAA00; } </style> <body style="font:normal 10px Arial,monospaced; margin:0; padding:0;"> Not able to stop the sequence.  <span class="d">(datetime)</span></body></html>'.replace('datetime', datetime.now().isoformat(' ', 'seconds'))
                self.ui.textBrowser.append(stop_log_html)

        
    def convertHDF5(self):
        while True:
            item = self.q.get()
            print(item)
            #execute a task: call a shell program and wait until it completes
            try:
                self.proc1 = subprocess.Popen(['python3', item], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                stdout, stderr = self.proc1.communicate()
                print(stdout)
            except FileNotFoundError as exc:
                print(f"Process failed because the executable could not be found.\n{exc}")
                return
            except subprocess.CalledProcessError as exc:
                print(f"Process failed because did not return a successful return code. " f"Returned {exc.returncode}\n{exc}")
                return
            if self.proc1.returncode == 0:
                self.conversion_success = 1
                print('Converted successfully!')
                self.ui.convert_button.setChecked(False)
                #self.ui.convert_button.setText("Convert data")
                self.toggleConvertButton()
                return
            #self.q.task_done()

    def start_sa1_sequence(self):
        try:
            pydoocs.write(self.sa1_sequence_prefix+'/RUN.ONCE', 1)
            start_log = datetime.now().isoformat(' ', 'seconds')+': Started Taskomat sequence.\n'
            start_log_html = '<html> <style> p { margin:0px; } span.d { font-size:80%; color:#555555; } span.e { font-weight:bold; color:#FF0000; } span.w { color:#CCAA00; } </style> <body style="font:normal 10px Arial,monospaced; margin:0; padding:0;"> Started the Taskomat sequence.  <span class="d">(datetime)</span></body></html>'.replace('datetime', datetime.now().isoformat(' ', 'seconds'))
            self.logstring.append(start_log)
            self.ui.textBrowser.append(start_log_html)
            self.ui.textEdit.textChanged.connect(self.updatetaskomatlogs)
            while pydoocs.read(self.sa1_sequence_prefix+'/RUNNING')['data'] == 1:
                self.ui.textEdit.setText(pydoocs.read(self.sa1_sequence_prefix+'/LOG.LAST')['data'])
                
                
                
                time.sleep(0.05)
            #    self.ui.lastlog.setText(pydoocs.read(self.sa1_sequence_prefix+'/LOG.LAST')['data'])
                 #pass
                
            self.updatetaskomatlogs()	 
            self.ui.sequence_button.setChecked(False)
            self.ui.sequence_button.setText("Start SASE 1 DAQ")
            
        except:
            print('Not able to start Taskomat sequence.')
            start_log = datetime.now().isoformat(' ', 'seconds')+': Not able to start Taskomat sequence.\n'
            start_log_html = '<html> <style> p { margin:0px; } span.d { font-size:80%; color:#555555; } span.e { font-weight:bold; color:#FF0000; } span.w { color:#CCAA00; } </style> <body style="font:normal 10px Arial,monospaced; margin:0; padding:0;"> Not able to start Taskomat sequence.  <span class="d">(datetime)</span></body></html>'.replace('datetime', datetime.now().isoformat(' ', 'seconds'))
            self.logstring.append(start_log)
            self.ui.textBrowser.append(start_log_html)
            self.ui.sequence_button.setChecked(False)
            self.ui.sequence_button.setText("Start SASE 1 DAQ")
        

    def updatetaskomatlogs(self):
        self.last_log_html = pydoocs.read(self.sa1_sequence_prefix+'/LOG_HTML.LAST')['data']
        self.last_log = pydoocs.read(self.sa1_sequence_prefix+'/LOG.LAST')['data']
        self.logstring.append(self.last_log+'\n')
        self.ui.textBrowser.append(self.last_log_html)


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

    def logbook_entry(self, text=""):
        """
        Method to send data + screenshot to eLogbook
        :return:
        """
        #screenshot = self.get_screenshot(widget)
        res = send_to_desy_elog(
            author="", title="SA1 DAQ Measurement", severity="INFO", text=text, elog="xfellog")
        if res == True:
            success_log_html = '<html> <style> p { margin:0px; } span.d { font-size:80%; color:#555555; } span.e { font-weight:bold; color:#FF0000; } span.w { color:#CCAA00; } </style> <body style="font:normal 10px Arial,monospaced; margin:0; padding:0;"> Finished scan! Logbook entry submitted. <span class="d">(datetime)</span></body></html>'.replace('datetime', datetime.now().isoformat(' ', 'seconds'))
            self.ui.textBrowser.append(success_log_html)
        if not res:
            error_log_html = '<html> <style> p { margin:0px; } span.d { font-size:80%; color:#555555; } span.e { font-weight:bold; color:#FF0000; } span.w { color:#CCAA00; } </style> <body style="font:normal 10px Arial,monospaced; margin:0; padding:0;"> Finished scan! Error sending eLogBook entry. <span class="d">(datetime)</span></body></html>'.replace('datetime', datetime.now().isoformat(' ', 'seconds'))
            self.ui.textBrowser.append(error_log_html)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = DAQApp()

    path = 'gui/xfel.png'
    app.setWindowIcon(QtGui.QIcon(path))
    window.show()
    window.raise_()

    sys.exit(app.exec_())
