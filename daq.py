import sys
import string
import os
import numpy as np
import pandas as pd
from os import listdir
from os.path import isfile, join
import h5py
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtWidgets import QWidget, QApplication, QFileDialog
from gui.UIdaq import Ui_Form
import threading, queue
import shutil
import re
from datetime import datetime, timedelta
from dateutil import tz
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
        self.ui.sequence_button.setCheckable(False)
        self.ui.sequence_button.setEnabled(False)
        #self.ui.sequence_button.clicked.connect(self.toggleSequenceButton)

        self.conversionSettings = {'starttime': 'start', 'stoptime': 'stop', 'bunchfilter': 'SA2'}
        self.ui.convert_button.clicked.connect(self.toggleConvertButton)
        self.ui.starttime.setDateTime(QDateTime.currentDateTime().addSecs(-60))
        self.ui.stoptime.setDateTime(QDateTime.currentDateTime())
        self.ui.starttime.setDisplayFormat("dd/MM/yyyy hh:mm:ss")
        self.ui.stoptime.setDisplayFormat("dd/MM/yyyy hh:mm:ss")
        self.ui.starttime.setMaximumDateTime(QDateTime.currentDateTime())
        self.ui.stoptime.setMaximumDateTime(QDateTime.currentDateTime())

        self.ui.radioButton.clicked.connect(self.check)
        self.ui.starttime.dateTimeChanged.connect(self.startdatetimeChanged)
        self.ui.stoptime.dateTimeChanged.connect(self.stopdatetimeChanged)
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

            if self.ui.radioButton.isChecked() == False:
                self.read_start_stop_time()
            self.ui.radioButton.setEnabled(False)
            self.ui.starttime.setEnabled(False)
            self.ui.stoptime.setEnabled(False)

            SASE = self.ui.SASEoptions.currentText()
            if SASE == 'SASE1':
                self.conversionSettings['bunchfilter'] = 'SA1'
            elif SASE == 'SASE2':
                self.conversionSettings['bunchfilter'] = 'SA2'
            elif SASE == 'SASE3':
                self.conversionSettings['bunchfilter'] = 'SA3'
            elif SASE == 'LINAC':
                self.conversionSettings['bunchfilter'] = 'all'

            cmd = 'python modules/level0v2.py'
            #self.command = cmd + ' --start ' + self.conversionSettings['starttime'] + ' --stop ' + self.conversionSettings['stoptime'] + ' --xmldfile ' + self.conversionSettings['xmldfile'] + ' --dest ' + self.conversionSettings['bunchfilter']
            self.command = cmd + ' --start ' + self.conversionSettings['starttime'] + ' --stop ' + self.conversionSettings['stoptime'] + ' --dest ' + self.conversionSettings['bunchfilter']
            print(self.command)
            self.q.put(self.command)
            t = threading.Thread(target=self.convertHDF5)
            t.daemon = True
            t.start()
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
                #self.logbook_entry(text=self.logbooktext)
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
                #self.logbook_entry(text=self.logbooktext)

    def toggleSequenceButton(self):
        # if button is checked
        if self.ui.sequence_button.isChecked():
            # setting background color to blue
            self.palette = self.ui.sequence_button.palette()
            self.palette.setColor(QtGui.QPalette.Button, QtGui.QColor('blue'))
            self.ui.sequence_button.setPalette(self.palette)
            self.ui.sequence_button.setText("Force Stop DAQ")

            #t = threading.Thread(target=self.start_sa1_sequence)
            #t.daemon = True
            #t.start()
            self.start_sa1_sequence()
            self.logbooktext = ''.join(self.logstring)
            #self.logbook_entry(widget=self.tab, text=self.logbooktext)

        # if it is unchecked
        else: # Force Stop
            # set background color back to white
            self.palette = self.ui.sequence_button.palette()
            self.palette.setColor(QtGui.QPalette.Button, QtGui.QColor('white'))
            self.ui.sequence_button.setPalette(self.palette)
            self.ui.sequence_button.setText("Start DAQ")
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
            #print(item)
            #execute a task: call a shell program and wait until it completes
            try:
                self.proc1 = subprocess.run(item, shell=True)
                #stdout, stderr = self.proc1.communicate()
                #print(stdout)
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
            while pydoocs.read(self.sa1_sequence_prefix+'/RUNNING')['data'] == 1:
                log = pydoocs.read(self.sa1_sequence_prefix+'/LOG.LAST')['data']
                if log not in self.ui.textBrowser.toPlainText():
                    self.ui.textBrowser.append(pydoocs.read(self.sa1_sequence_prefix+'/LOG_HTML.LAST')['data'])
                    self.logstring.append(pydoocs.read(self.sa1_sequence_prefix+'/LOG.LAST')['data']+'\n')
                    time.sleep(0.01)
                 #pass
            self.update_taskomat_logs()
            self.ui.sequence_button.setChecked(False)
            self.palette = self.ui.sequence_button.palette()
            self.palette.setColor(QtGui.QPalette.Button, QtGui.QColor('white'))
            self.ui.sequence_button.setPalette(self.palette)
            self.ui.sequence_button.setText("Start SASE 1 DAQ")
        except:
            print('Not able to start Taskomat sequence.')
            start_log = datetime.now().isoformat(' ', 'seconds')+': Not able to start Taskomat sequence.\n'
            start_log_html = '<html> <style> p { margin:0px; } span.d { font-size:80%; color:#555555; } span.e { font-weight:bold; color:#FF0000; } span.w { color:#CCAA00; } </style> <body style="font:normal 10px Arial,monospaced; margin:0; padding:0;"> Not able to start Taskomat sequence.  <span class="d">(datetime)</span></body></html>'.replace('datetime', datetime.now().isoformat(' ', 'seconds'))
            self.logstring.append(start_log)
            self.ui.textBrowser.append(start_log_html)
            self.ui.sequence_button.setChecked(False)
            self.ui.sequence_button.setText("Start SASE 1 DAQ")


    def update_taskomat_logs(self):
        self.last_log_html = pydoocs.read(self.sa1_sequence_prefix+'/LOG_HTML.LAST')['data']
        self.last_log = pydoocs.read(self.sa1_sequence_prefix+'/LOG.LAST')['data']
        self.logstring.append(self.last_log+'\n')
        self.ui.textBrowser.append(self.last_log_html)

    def read_start_stop_time(self):
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('Europe/Vienna')
        start_time_utc = pydoocs.read(self.sa1_sequence_prefix+'/STEP007.EXECUTION')['data']
        stop_time_utc = pydoocs.read(self.sa1_sequence_prefix+'/STEP008.EXECUTION')['data']

        # Tell the datetime object that it's in UTC time zone since
        # datetime objects are 'naive' by default
        utc_t1 = datetime.strptime(start_time_utc, '%Y-%m-%d %H:%M:%S UTC')
        utc_t1 = utc_t1.replace(tzinfo=from_zone) - timedelta(seconds=5)

        utc_t2 = datetime.strptime(stop_time_utc, '%Y-%m-%d %H:%M:%S UTC')
        utc_t2 = utc_t2.replace(tzinfo=from_zone) - timedelta(seconds=1)

        # Convert time zone and change to isoformat
        self.conversionSettings['starttime'] = utc_t1.astimezone(to_zone).replace(tzinfo=None).isoformat()
        self.conversionSettings['stoptime'] = utc_t2.astimezone(to_zone).replace(tzinfo=None).isoformat()
        print(self.conversionSettings['starttime'], self.conversionSettings['stoptime'])
        #self.logstring.append(self.last_log+'\n')
        #self.ui.textBrowser.append(self.last_log_html)

    # method called by radio button
    def check(self):
        # checking if it is checked
        if self.ui.radioButton.isChecked():
            # changing text of label
            self.ui.starttime.setEnabled(True)
            self.ui.stoptime.setEnabled(True)

        # if it is not checked
        else:
            self.ui.starttime.setEnabled(False)
            self.ui.stoptime.setEnabled(False)

    def startdatetimeChanged(self):
        self.conversionSettings['starttime'] = self.ui.starttime.dateTime().toString('yyyy-MM-ddTHH:mm:ss')

    def stopdatetimeChanged(self):
        self.conversionSettings['stoptime'] = self.ui.stoptime.dateTime().toString('yyyy-MM-ddTHH:mm:ss')

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
