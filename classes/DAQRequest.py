import sys
import os
import xml.etree.ElementTree as ET
import re
import datetime 



def get_key_by_value(a, v):
    for key, value in a.iteritems():
        if value == v:
            return key
    return None

class  DAQRequest:
    
    def __init__(self, xmlfile=''):
        # constants for Scan Mode
        self.TTF2_DAQ_SCAN_BY_TIME = 0x10000000
        self.TTF2_DAQ_GIVE_WHAT_YOU_HAVE = 0x20000000
        self.TTF2_DAQ_SCANM_FILES_SHIFT = 4
        self.TTF2_DAQ_SCANM_ALL = 15
        self.TTF2_DAQ_SCANM_MAX = self.TTF2_DAQ_SCANM_ALL

        # definitions of Request Types
        self.daqrequesttype =  {
            'TTF2_DAQ_REQ_DATA':1,
            'TTF2_DAQ_REQ_CHAN_LIST':2,
            'TTF2_DAQ_REQ_STAT':3
        }

        # Definitions of communication type
        self.daqcomtype = {
        'TTF2_DAQ_COMM_PUSH':1,
        'TTF2_DAQ_COMM_HNDS':2
        }

        # members
        self.listtags = ['Chan', 'File']
        self.intags = ['ReqId', 'RunFirst', 'RunLast', 'ScanMode', 'ReqType', 'CommMode']
        self.request = {'ReqId':None, 'TStart':None,  'TStop':None, 'RunFirst':None, 'RunLast':None, 'Exp':None, 'DDir':None, 'CDir':None, 'Chan':None, 'File':None, 'ScanMode':None, 'ReqType':None, 'CommMode':None, 'ConfFile':None} 
        self.xmlfile = xmlfile

        # initialization
        self.roottag = 'DAQREQ'
        if(self.xmlfile == '' or not os.path.exists(self.xmlfile)) or (not os.access(self.xmlfile, os.R_OK)):
            raise Exception("Something wrong with XML file " + self.xmlfile)

        tree = ET.parse(self.xmlfile)
        
        root = tree.getroot()                                                 
        if root.tag != self.roottag:
            raise Exception("Root tag (%s) is invalid in XML file %s (must be %s) "%(root.tag,self.xmlfile, self.roottag))
        for elem in root:
           #print(elem.tag)
            if elem.tag in self.request:
                #print(elem.tag, ":",elem.text, elem.attrib)
                if elem.tag in self.listtags: 
                    if not self.request[elem.tag]:
                        self.request[elem.tag] = []
                    self.request[elem.tag].append(elem.attrib)
                else:
                    self.request[elem.tag] = elem.attrib
                #for attr in  elem.attrib:
                #    print(attr.name, ":",attr.text  )
        self.request['ConfFile'] = {'file': xmlfile}

    def getReqId(self):
        if self.request['ReqId']:
            return int(self.request['ReqId']['id'])
        return None

    def getRunFirst(self):
        if self.request['RunFirst']:
            return int(self.request['RunFirst']['number'])
        return None
    
    def getRunLast(self):
        if self.request['RunLast']:
            return int(self.request['RunLast']['number'])
        return None

    def getStartTime(self):
        if self.request['TStart']:
            return self.request['TStart']['time']
        return None

    def setStartTime(self, tm):
        if not isinstance(tm,str):
            return True
        old  = ''
        if self.request['TStart']:
            old = self.request['TStart']['time']
            self.request['TStart']['time'] = tm
        else:
            self.request['TStart'] = {'time':tm}
        try:
            self.getStartTimeSec()
        except Exception as Err:
            if old == '':
                self.request['TStart'] =  None
            else:
                self.request['TStart']['time'] = old
            return True
        return False

    def getStartTimeSec(self):
        if self.request['TStart']:
            tm =  self.request['TStart']['time']
            return int(datetime.datetime.strptime(tm, '%Y-%m-%dT%H:%M:%S').timestamp())
        return None

    def getStopTime(self):
        if self.request['TStop']:
            return self.request['TStop']['time']
        return None

    def getStopTimeSec(self):
        if self.request['TStop']:
            tm =  self.request['TStop']['time']
            return int(datetime.datetime.strptime(tm, '%Y-%m-%dT%H:%M:%S').timestamp())
        return None
    
    def setStopTime(self, tm):
        if not isinstance(tm,str):
            return True
        old  = ''
        if self.request['TStop']:
            old = self.request['TStop']['time']
            self.request['TStop']['time'] = tm
        else:
            self.request['TStop'] = {'time':tm}
        try:
            self.getStopTimeSec()
        except Exception as Err:
            if old == '':
                self.request['TStop'] =  None
            else:
                self.request['TStop']['time'] = old
            return True
        return False

    def getDataDir(self):
        if self.request['DDir']:
            return self.request['DDir']['name']
        return None

    def getControlDir(self):
        if self.request['CDir']:
            return self.request['CDir']['name']
        return None

    def getExp(self):
        if self.request['Exp']:
            return self.request['Exp']['name']
        return None

    def getScanMode(self):
        if self.request['ScanMode']:
            return int(self.request['ScanMode']['mode'])
        return None

    def getReqType(self):
        if self.request['ReqType']:
            return int(self.request['ReqType']['type'])
        return None
    
    def getCommMode(self):
        if self.request['CommMode']:
            return int(self.request['CommMode']['mode'])
        return None

    def getConfFile(self):
        if self.request['ConfFile']:
            return self.request['ConfFile']['file']
        return None
    
    def getChans(self):
        if self.request['Chan']:
            out = []
            for chan in self.request['Chan']:
                out.append(chan['name'])
            return out
        return None

    def setChans(self, chans):
        if isinstance(chans, list):
            self.request['Chan'] = chans
        return self.getChans()

    def getFiles(self):
        if self.request['File']:
            out = []
            for chan in self.request['File']:
                out.append(chan['name'])
            return out
        return None


    def printRaw(self):
        print(self.request)

    def print(self):
        if self.getReqId():
            print('ReqId:\t%d'%(self.getReqId()))
        if self.getStartTime():
            print('Start:\t%s (%d)'%(self.getStartTime(),self.getStartTimeSec()))
        if self.getStopTime():
            print('Stop:\t%s (%d)'%(self.getStopTime(),self.getStopTimeSec()))
        if self.getRunFirst():
            print('Run first:\t%d'%(self.getRunFirst()))
        if self.getRunLast():
            print('Run last:\t%d'%(self.getRunLast()))
        if self.getExp():
            print('Exp.:\t%s'%(self.getExp()))
        if self.getDataDir():
            print('DDir.:\t%s'%(self.getDataDir()))  
        if self.getControlDir():
            print('CDir.:\t%s'%(self.getControlDir()))
        if self.getReqType():
            key = get_key_by_value(self.daqrequesttype, self.getReqType())
            if key:
                print('Request:\t%s'%(key))
            else:
                print('Request:\tUnknown') 
        if self.getCommMode():
            key = get_key_by_value(self.daqcomtype, self.getCommMode())
            if key:
                print('Com.Mode:\t%s'%(key))
            else:
                print('Com.Mode:\tUnknown')
        if self.getScanMode():
            mode = self.getScanMode()
            print('ScnaMode:\t', end=' ')
            if mode and self.TTF2_DAQ_SCAN_BY_TIME:
                print('Synch by time', end=' ')
            else:
                print('Synch by EvId', end=' ')
            if mode and self.TTF2_DAQ_GIVE_WHAT_YOU_HAVE:
                print('Not all channel present', end=' ')
            else:
                print('All channel present', end=' ')
            jump = mode  & (~self.TTF2_DAQ_SCAN_BY_TIME) & (~self.TTF2_DAQ_GIVE_WHAT_YOU_HAVE)  
            jump = jump >> self.TTF2_DAQ_SCANM_FILES_SHIFT
            if jump:
                print("Event jump: %d"%(jump))
        if self.getChans():
            print('Requested channels:')
            for chan in self.getChans():
                print('\t',chan)
        if self.getFiles():
            print('Requested files:')
            for file in self.getFiles():
                print('\t',file)
        if self.getConfFile():
            print('XML file: %s'%(self.getConfFile()))


    def create_xml(self, filename):
        out = "<DAQREQ>\n"
        
        for key in self.request.keys():
            if self.request[key]:
                if isinstance(self.request[key],list):
                    for entry in self.request[key]:
                        out += '<' + key
                        for enkey in entry.keys():
                            out += ' ' + enkey + "='" + entry[enkey] + "'"
                        out += "/>\n"
                else:
                    out += "<"
                    out += key 
                    for inkey in self.request[key]:
                        out += ' '+ inkey + "='" + self.request[key][inkey] + "'"
                        out += "/>\n"
        out += "</DAQREQ>\n"
        write_status = None
        if filename:
             if isinstance(filename,str):
                try:
                    with open(filename, 'w') as writer:
                        writer.write(out)
                        write_status = True
                except Exception as err:
                    write_status = False
        return out, write_status
