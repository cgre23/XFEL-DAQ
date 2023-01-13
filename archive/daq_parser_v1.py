import sys
import string
import os
import subprocess
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QApplication, QFileDialog
from gui.UI_daq import Ui_Form
import shutil
#import classes.trie as trie
#from collections import defaultdict


class DAQApp(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        # Initialize parameters
        self.daterange = 0
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.filtertable.setRowCount(0)
        self.ui.filtertable.setColumnCount(1)
        self.ui.filtertable.horizontalHeader().setStretchLastSection(True)
        self.channel_list = []
        self.channel_group_list = []
        self.channels_selected = []
        self.rawfilepathlist = []
        self.streampath = ''
        self.localmode = False

        # Disable buttons
        self.ui.loadcataloguepb.setEnabled(False)
        self.ui.channelpb.setEnabled(False)
        self.ui.pushButton.setEnabled(False)
        self.ui.filterpb.setEnabled(False)
        self.ui.rawFileSelectpb.setEnabled(False)
        self.xml_name_matches = ["main", "run", "chan", "dscr", ".xml"]

        # Timestamp
        self.ui.startdate.setDateTime(QtCore.QDateTime.currentDateTime())
        self.ui.stopdate.setDateTime(
            QtCore.QDateTime.currentDateTime())
        self.ui.startdate.setDisplayFormat("dd/MM/yyyy hh:mm:ss")
        self.ui.stopdate.setDisplayFormat("dd/MM/yyyy hh:mm:ss")

        # Push buttons
        self.ui.browsepb.clicked.connect(self.open_file)
        self.ui.rawFileSelectpb.clicked.connect(self.open_raw_files)
        self.ui.channelpb.clicked.connect(self.getChannelList)
        self.ui.browsepb2.clicked.connect(self.open_file_catalogue)
        self.ui.loadcataloguepb.clicked.connect(self.getChannelListCatalogue)
        self.ui.pushButton.clicked.connect(self.find_checked)
        self.ui.filterpb.clicked.connect(self.find_checked_filters)
        self.ui.localmoderb.toggled.connect(self.local_mode)

        # table/ tree headers
        header = self.ui.treeWidget_2.header()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.ui.treeWidget.setHeaderLabels(['Channel name'])
        self.ui.treeWidget_2.setHeaderLabels(
            ['Channel name', 'Description', 'Unit'])
        self.ui.filtertable.setHorizontalHeaderLabels(['Filter by subsystem:'])
        self.ui.filtertable.setFont(QtGui.QFont('Arial', 10))
        # Catalogue Search bar
        self.ui.searchbar.setEnabled(False)
        self.ui.searchbar.setPlaceholderText("Search...")
        self.ui.searchbar.textChanged.connect(self.search_bar)

    def getChannelList(self):
        #Open XML file Tab 1
        self.ui.treeWidget.clear()
        self.channel_list = []
        fname = self.streampath
        self.ui.pushButton.setEnabled(
            self.check_xml_filename(self.streampath))
        if(fname != None and fname != ''):
            self.fname = fname
            f = QtCore.QFile(fname)
            f.open(QtCore.QIODevice.ReadOnly)
            xml = QtCore.QXmlStreamReader(f)
            while(xml.atEnd() != True):
                xml.readNext()
                if(xml.isStartDocument()):
                    continue
                if(xml.isStartElement()):
                    if(xml.name() == "NAME"):
                        self.channel = str(xml.readElementText())
                        self.channel_list.append(self.channel)
                        self.add_items()
                    if(xml.name() == "SUBSYSTEM"):
                        self.channel_group = str(xml.readElementText())
                        self.channel_group_list.append(self.channel_group)
                #elif(xml.isEndElement()):
            xml.clear()
            f.close()
        #keys = self.channel_group_list
        #values = self.channel_list
        #self.clusters = defaultdict(list)
        #self.clusters['Select all'] = self.channel_list
        #for i, j in zip(keys, values):
        #    self.clusters[i].append(j)
        #self.fill_filter_table()
        self.clusters_check()

    def getChannelListCatalogue(self):
        self.ui.treeWidget_2.clear()
        fname = self.streampath_cat

        if(fname != None and fname != ''):
            self.fname = fname
            f = QtCore.QFile(fname)
            f.open(QtCore.QIODevice.ReadOnly)
            xml = QtCore.QXmlStreamReader(f)
            while(xml.atEnd() != True):
                xml.readNext()
                if(xml.isStartDocument()):
                    continue
                if(xml.isStartElement()):
                    if(xml.name() == "NAME"):
                        self.channel = str(xml.readElementText())
                        self.channel_list.append(str(xml.readElementText()))
                        rowcount = self.ui.treeWidget_2.topLevelItemCount()
                        item = QtWidgets.QTreeWidgetItem(rowcount)
                        self.ui.treeWidget_2.addTopLevelItem(item)
                        self.ui.treeWidget_2.topLevelItem(
                            rowcount).setText(0, self.channel)
                        self.ui.treeWidget_2.topLevelItem(rowcount).setFlags(
                            self.ui.treeWidget_2.topLevelItem(rowcount).flags() | QtCore.Qt.ItemIsUserCheckable)
                        self.ui.treeWidget_2.topLevelItem(
                            rowcount).setTextAlignment(0, QtCore.Qt.AlignLeft)
                    if(xml.name() == "UNITS"):
                        self.channel_unit = str(xml.readElementText())
                        self.ui.treeWidget_2.topLevelItem(
                            rowcount).setText(2, self.channel_unit)
                    if(xml.name() == "DESC"):
                        self.channel_descriptions = str(xml.readElementText())
                        self.ui.treeWidget_2.topLevelItem(
                            rowcount).setText(1, self.channel_descriptions)
                    if(xml.name() == "DIM_NAME"):
                        self.dim_names = str(xml.readElementText())
                    if(xml.name() == "DIM_UNITS"):
                        self.dim_units = str(xml.readElementText())
                    if(xml.name() == "DIM_DESCR"):
                        self.dim_descriptions = str(xml.readElementText())
                        child = QtWidgets.QTreeWidgetItem(
                            [self.dim_names, self.dim_descriptions, self.dim_units])
                        item.addChild(child)
                #elif(xml.isEndElement()):
            xml.clear()
            f.close()
        self.ui.searchbar.setEnabled(True)

    def add_items(self):
        rowcount = self.ui.treeWidget.topLevelItemCount()
        item = QtWidgets.QTreeWidgetItem(rowcount)
        self.ui.treeWidget.addTopLevelItem(item)
        self.ui.treeWidget.topLevelItem(
            rowcount).setText(0, self.channel)
        self.ui.treeWidget.topLevelItem(
            rowcount).setCheckState(0, QtCore.Qt.Unchecked)
        self.ui.treeWidget.topLevelItem(rowcount).setFlags(
            self.ui.treeWidget.topLevelItem(rowcount).flags() | QtCore.Qt.ItemIsUserCheckable)
        self.ui.treeWidget.topLevelItem(
            rowcount).setTextAlignment(0, QtCore.Qt.AlignLeft)

    def clusters_check(self):
        self.clusters = {}
        self.clusters['Select all'], self.clusters['BPM'], self.clusters['BAM'], self.clusters['BCM'], self.clusters['XGM'], self.clusters['TOROID'], self.clusters[
            'DAQ_INFO'], self.clusters['XGM_PROPERTIES'], self.clusters['SA1'], self.clusters['SA2'], self.clusters['SA3'], self.clusters['RF'], \
            self.clusters['TIMINGINFO'],  self.clusters['MAGNET'], self.clusters['HOLDDMA'], self.clusters['CHICANE'], self.clusters['UNDULATOR'], \
            self.clusters['BEAM_ENERGY_MEASUREMENT'],  self.clusters['CHARGE'], self.clusters['HOLDSCOPE'], self.clusters['BHM'], self.clusters['KICKER'], \
            self.clusters['FARADAY'],  self.clusters['DCM'], self.clusters['BLM'] \
            = [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []
        self.clusters['Select all'] = self.channel_list
        for channel in self.channel_list:
            if channel.find('BPM') != -1:
                self.clusters['BPM'].append(channel)
            if channel.find('BAM.DAQ') != -1:
                self.clusters['BAM'].append(channel)
            if channel.find('BCM/BCM') != -1:
                self.clusters['BCM'].append(channel)
            if channel.find('XGM/XGM') != -1:
                self.clusters['XGM'].append(channel)
            if channel.find('TOROID') != -1:
                self.clusters['TOROID'].append(channel)
            if channel.find('DISTRIBUTOR') != -1:
                self.clusters['DAQ_INFO'].append(channel)
            if channel.find('XGM.POSMON') != -1 or channel.find('XGM.CURRENT') != -1 or channel.find('XGM.TEMP') != -1 or channel.find('XGM.PHOTONFLUX') != -1 or channel.find('XGM.GAS') != -1 or channel.find('XGM.PRESSURE') != -1:
                self.clusters['XGM_PROPERTIES'].append(channel)
            if channel.find('SA1') != -1:
                self.clusters['SA1'].append(channel)
            if channel.find('SA2') != -1:
                self.clusters['SA2'].append(channel)
            if channel.find('SA3') != -1:
                self.clusters['SA3'].append(channel)
            if channel.find('TIMINGINFO') != -1:
                self.clusters['TIMINGINFO'].append(channel)
            if channel.find('MAGNETS/MAGNET') != -1:
                self.clusters['MAGNET'].append(channel)
            if channel.find('HOLDDMA') != -1:
                self.clusters['HOLDDMA'].append(channel)
            if channel.find('CHICANE') != -1:
                self.clusters['CHICANE'].append(channel)
            if channel.find('UNDULATOR') != -1:
                self.clusters['UNDULATOR'].append(channel)
            if channel.find('RF/MODULATOR') != -1:
                self.clusters['RF'].append(channel)
            if channel.find('BEAM_ENERGY_MEASUREMENT') != -1:
                self.clusters['BEAM_ENERGY_MEASUREMENT'].append(channel)
            if channel.find('CHARGE.ML') != -1:
                self.clusters['CHARGE'].append(channel)
            if channel.find('HOLDSCOPE') != -1:
                self.clusters['HOLDSCOPE'].append(channel)
            if channel.find('BHM/BHM') != -1:
                self.clusters['BHM'].append(channel)
            if channel.find('KICKER.ADC') != -1:
                self.clusters['KICKER'].append(channel)
            if channel.find('FARADAY') != -1:
                self.clusters['FARADAY'].append(channel)
            if channel.find('DCM/DCM') != -1:
                self.clusters['DCM'].append(channel)
            if channel.find('BLM/BLM') != -1:
                self.clusters['BLM'].append(channel)
        self.fill_filter_table()

    def find_checked(self):
        self.checked_list = list()
        root = self.ui.treeWidget.invisibleRootItem()
        signal_count = root.childCount()
        if signal_count > 0:
            for i in range(signal_count):
                signal = root.child(i)
                if signal.checkState(0) == QtCore.Qt.Checked:
                    self.checked_list.append(signal.text(0))
            self.ui.status_text.setText(
                'Creating XML file with selected channels')
            if self.ui.localmoderb.isChecked() and self.localmode:
                filename_ok = self.check_raw_filename()
                if filename_ok:
                    self.create_xml()
                else:
                    self.ui.status_text.setText(
                        'Make sure all raw files are from the same stream')
            else:
                self.create_xml()
        else:
            self.ui.status_text.setText('No channels selected')

    def find_checked_filters(self):
        self.checked_filter_list = []
        selected_channels = []
        for i in range(self.ui.filtertable.rowCount()):
            if self.ui.filtertable.item(i, 0).checkState() == QtCore.Qt.Checked:
                self.checked_filter_list.append(
                    self.ui.filtertable.item(i, 0).text())
            else:
                pass
        selected_channels = [self.clusters[x]
                             for x in self.checked_filter_list]
        flat_list = [item for sublist in selected_channels for item in sublist]
        # Uncheck current items
        root = self.ui.treeWidget.invisibleRootItem()
        signal_count = root.childCount()
        if signal_count > 0:
            for i in range(signal_count):
                signal = root.child(i)
                if signal.checkState(0) == QtCore.Qt.Checked:
                    signal.setCheckState(0, QtCore.Qt.Unchecked)
        # Check items in filter
        for channel in flat_list:
            matching_items = self.ui.treeWidget.findItems(
                channel, Qt.MatchExactly)
            if matching_items:
                # We have found something.
                item = matching_items[0]  # Take the first.
                item.setCheckState(0, QtCore.Qt.Checked)

    def create_xml(self):
        inner_template = string.Template('<Chan name="${name}"/>')
        inner_template_filelist = string.Template('<File name="${filename}"/>')
        data = self.checked_list
        stream_name = str(self.ui.filenameEdit.text()).split('_main')[0]

        if self.ui.localmoderb.isChecked() and self.localmode:
            outer_template_raw = string.Template("""<DAQREQ>
            <Exp  name='${exp}'/>
            ${filename_list}
            ${document_list}
            <CDir name='/daq/xfel/admtemp' />
            </DAQREQ>
             """)
            inner_contents_filelist = [inner_template_filelist.substitute(
                filename=path) for path in self.rawfilepathlist]
            inner_contents = [inner_template.substitute(
                name=channel) for channel in data]
            result = outer_template_raw.substitute(
                filename_list='\n'.join(inner_contents_filelist), document_list='\n'.join(inner_contents), exp=stream_name)
        else:
            outer_template = string.Template("""<DAQREQ>
            <TStart time='${starttime}'/>
            <TStop  time='${stoptime}'/>
            <Exp  name='${exp}'/>
            ${document_list}
            <CDir name='/daq/xfel/admtemp' />
            </DAQREQ>
             """)
            start_timestamp = self.ui.startdate.dateTime()
            start_timestamp_str = start_timestamp.toString(
                'yyyy-MM-ddTHH:mm:ss')
            stop_timestamp_min = start_timestamp.addSecs(1)
            self.ui.stopdate.setMinimumDateTime(stop_timestamp_min)
            stop_timestamp = self.ui.stopdate.dateTime().toString('yyyy-MM-ddTHH:mm:ss')
            inner_contents = [inner_template.substitute(
                name=channel) for channel in data]
            result = outer_template.substitute(
                document_list='\n'.join(inner_contents), exp=stream_name, starttime=start_timestamp_str, stoptime=stop_timestamp)
        self.makedirs('temp')
        filename = 'temp/filtered_stream_channels.xml'
        self.write_status = None
        try:
            with open(filename, 'w') as writer:
                writer.write(result)
                self.write_status = True
        except Exception as err:
            self.write_status = False
        self.copy_xml_desc_file()
        self.launch_script()
        #self.deletedirs()

    def open_file(self):  # self.parent.data_dir
        self.streampath, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Pick channel description file", "/daq/xfel/admtemp", 'xml (*.xml)', None, QtWidgets.QFileDialog.DontUseNativeDialog)
        if self.streampath != "":
            filename = os.path.basename(self.streampath)
            self.ui.filenameEdit.setText(filename)
            self.ui.channelpb.setEnabled(
                self.check_xml_filename(self.streampath))
        else:
            self.ui.filenameEdit.setText('')

    def open_raw_files(self):  # self.parent.data_dir
        self.rawfilepathlist, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Pick raw files", "/pnfs/desy.de/xfel", 'raw (*.raw)', None, QtWidgets.QFileDialog.DontUseNativeDialog)
        if self.rawfilepathlist != []:
            print(self.rawfilepathlist)
            list_len = len(self.rawfilepathlist)
            self.ui.filesSelected.setText('%d file(s) selected' % (list_len))
            self.localmode = True
            # Do Action
        else:
            self.ui.filesSelected.setText('No files selected')
            self.localmode = False

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

    def fill_filter_table(self):
        self.ui.filtertable.setRowCount(0)
        for row, key in enumerate(self.clusters):
            if self.clusters[key] == []:
                pass
            else:
                rowPosition = self.ui.filtertable.rowCount()
                self.ui.filtertable.insertRow(rowPosition)  # insert new row
                chkBoxItem = QtWidgets.QTableWidgetItem(key)
                chkBoxItem.setText(key)
                chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable
                                    | QtCore.Qt.ItemIsEnabled)
                chkBoxItem.setCheckState(QtCore.Qt.Unchecked)
                self.ui.filtertable.setItem(
                    rowPosition, 0, chkBoxItem)
        self.ui.filterpb.setEnabled(True)

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

    def filter_by_group(self, group):
        # Clear current selection.
        self.ui.treeWidget_2.setCurrentItem(None)
        if not group:
            # Empty string, don't search.
            return
        matching_items = self.ui.treeWidget_2.findItems(
            group, Qt.MatchContains)
        if matching_items:
            # We have found something.
            item = matching_items[0]  # Take the first.
            self.ui.treeWidget_2.setCurrentItem(item)

    def local_mode(self):
        if self.ui.localmoderb.isChecked():
            self.ui.rawFileSelectpb.setEnabled(True)
            self.ui.startdate.setEnabled(False)
            self.ui.stopdate.setEnabled(False)
            self.ui.status_text.setText('Local mode enabled')
        else:
            self.ui.rawFileSelectpb.setEnabled(False)
            self.ui.startdate.setEnabled(True)
            self.ui.stopdate.setEnabled(True)
            self.ui.status_text.setText('Local mode disabled')

    def launch_script(self):
        subprocess.call(['sh', './xfelhdf5.sh'])
        self.ui.status_text.setText(
            'Script file running. Data output directory: /Documents/DAQ_files/HDF5')

    def check_xml_filename(self, path):
        if all(x in path for x in self.xml_name_matches):
            return True
        else:
            return False

    def check_raw_filename(self):
        root_list = []
        for filename in self.rawfilepathlist:
            root_list.append(filename.split('_main')[0])
        root_item = root_list[0]
        print(root_list)
        for root in root_list:
            if root != root_item:
                return False
                break
            else:
                pass
        return True

    def copy_xml_desc_file(self):
        srcPath = self.streampath
        dest = os.getcwd() + '/temp/'
        destFile = 'chann_dscr.xml'
        destPath = os.path.join(dest, destFile)
        print(destPath)
        try:
            shutil.copy(srcPath, destPath)
            print("File copied successfully.")
        # If source and destination are same
        except shutil.SameFileError:
            print("Source and destination represents the same file.")
        # If there is any permission issue
        except PermissionError:
            print("Permission denied.")
        # For other errors
        except:
            print("Error occurred while copying file.")

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

"""
    def clusters_check(self):
        self.clusters = {}
        self.clusters['Select all'], self.clusters['BPM'], self.clusters['BAM'], self.clusters['BCM'], self.clusters['XGM'], self.clusters['TOROID'], self.clusters[
            'DAQ_INFO'], self.clusters['XGM_PROPERTIES'], self.clusters['SA1'], self.clusters['SA2'], self.clusters['SA3'], self.clusters['RF'], \
            self.clusters['TIMINGINFO'],  self.clusters['MAGNET'], self.clusters['HOLDDMA'], self.clusters['CHICANE'], self.clusters['UNDULATOR'], \
            self.clusters['BEAM_ENERGY_MEASUREMENT'],  self.clusters['CHARGE'], self.clusters['HOLDSCOPE'], self.clusters['BHM'], self.clusters['KICKER'], \
            self.clusters['FARADAY'],  self.clusters['DCM'], self.clusters['BLM'] \
            = [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []
        self.clusters['Select all'] = self.channel_list
        for channel in self.channel_list:
            if channel.find('BPM') != -1:
                self.clusters['BPM'].append(channel)
            if channel.find('BAM.DAQ') != -1:
                self.clusters['BAM'].append(channel)
            if channel.find('BCM/BCM') != -1:
                self.clusters['BCM'].append(channel)
            if channel.find('XGM/XGM') != -1:
                self.clusters['XGM'].append(channel)
            if channel.find('TOROID') != -1:
                self.clusters['TOROID'].append(channel)
            if channel.find('DISTRIBUTOR') != -1:
                self.clusters['DAQ_INFO'].append(channel)
            if channel.find('XGM.POSMON') != -1 or channel.find('XGM.CURRENT') != -1 or channel.find('XGM.TEMP') != -1 or channel.find('XGM.PHOTONFLUX') != -1 or channel.find('XGM.GAS') != -1 or channel.find('XGM.PRESSURE') != -1:
                self.clusters['XGM_PROPERTIES'].append(channel)
            if channel.find('SA1') != -1:
                self.clusters['SA1'].append(channel)
            if channel.find('SA2') != -1:
                self.clusters['SA2'].append(channel)
            if channel.find('SA3') != -1:
                self.clusters['SA3'].append(channel)
            if channel.find('TIMINGINFO') != -1:
                self.clusters['TIMINGINFO'].append(channel)
            if channel.find('MAGNETS/MAGNET') != -1:
                self.clusters['MAGNET'].append(channel)
            if channel.find('HOLDDMA') != -1:
                self.clusters['HOLDDMA'].append(channel)
            if channel.find('CHICANE') != -1:
                self.clusters['CHICANE'].append(channel)
            if channel.find('UNDULATOR') != -1:
                self.clusters['UNDULATOR'].append(channel)
            if channel.find('RF/MODULATOR') != -1:
                self.clusters['RF'].append(channel)
            if channel.find('BEAM_ENERGY_MEASUREMENT') != -1:
                self.clusters['BEAM_ENERGY_MEASUREMENT'].append(channel)
            if channel.find('CHARGE.ML') != -1:
                self.clusters['CHARGE'].append(channel)
            if channel.find('HOLDSCOPE') != -1:
                self.clusters['HOLDSCOPE'].append(channel)
            if channel.find('BHM/BHM') != -1:
                self.clusters['BHM'].append(channel)
            if channel.find('KICKER.ADC') != -1:
                self.clusters['KICKER'].append(channel)
            if channel.find('FARADAY') != -1:
                self.clusters['FARADAY'].append(channel)
            if channel.find('DCM/DCM') != -1:
                self.clusters['DCM'].append(channel)
            if channel.find('BLM/BLM') != -1:
                self.clusters['BLM'].append(channel)
        self.fill_filter_table()

    def clustering(self):
        # max number of strings per cluster
        MAX_NB_STRINGS_PER_CLUSTER = 50
        # result dict
        self.clusters = {}
        # add strings to trie
        print(self.channel_list)
        root = trie.TrieNode('', None)
        for string in self.channel_list:
            trie.add(root, string)

        # get clusters from trie
        clusters_nodes = []
        trie.chunk_into_clusters(
            root, MAX_NB_STRINGS_PER_CLUSTER, clusters_nodes)

        # get strings associated with each clusters nodes
        for cluster_node in clusters_nodes:
            cluster_node_string = trie.retrieve_string(cluster_node)

            self.clusters[cluster_node_string] = []

            # get strings contained in each cluster
            end_nodes = []
            trie.find_end_nodes(cluster_node, end_nodes)

            if cluster_node.is_string_finished:
                self.clusters[cluster_node_string].append(cluster_node_string)

            for end_node in end_nodes:
                end_node_string = trie.retrieve_string(end_node)
                self.clusters[cluster_node_string].append(end_node_string)

        # print results
        for cluster_name, cluster_strings in self.clusters.items():
            print("\n{}:".format(cluster_name))
            for string in cluster_strings:
                print("\t{}".format(string))
"""
