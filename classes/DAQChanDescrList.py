import sys
import os
import xml.etree.ElementTree as ET
import re
import classes.DAQChanDescr as DAQChanDescr
import datetime




class  ChanDescrList:
    
    def __init__(self, xmlfile = "", chans=[], chandescrlst=[]):
        self.chans = chans                     # channels to extract, if [] - all
        self.xmlfile = xmlfile
        self.chandescrlst  = []
        if chandescrlst == [] and ((self.xmlfile == '' or not os.path.exists(self.xmlfile)) or (not os.access(self.xmlfile, os.R_OK) )):
            raise Exception("Something wrong with XML file OR channel description list is empty" + self.xmlfile)

        if chandescrlst != []:
            self.chandescrlst = chandescrlst
            return
        tree = ET.parse(self.xmlfile)
        root = tree.getroot()     
        dims = 0
        bits = 0                                            
        for elem in root:
            #print(elem.tag)
            if elem.tag == 'CHANNEL':
                if  DAQChanDescr.tags['NAME'] != '':
                    #creating a new chan description
                    #tags['DIM'] = dims
                    #tags['BIT'] = bits
                    if dims:
                        DAQChanDescr.tags['DIM'].update({'DIMS':dims})
                    if bits:
                        DAQChanDescr.tags['BIT'].update({'BITS':bits})
                    dims = 0
                    bits = 0 
                    chd = DAQChanDescr.DAQChanDescr(chan = DAQChanDescr.tags)
                    if self.chans == [] or chd.get_name() in self.chans:
                        self.chandescrlst.append(chd)
                    DAQChanDescr.allcleanup()
            for subelem in elem:
                if subelem.tag in DAQChanDescr.tags:
                    #print(subelem.tag, ":",subelem.text )
                    if subelem.tag not in DAQChanDescr.internaltags:
                        if subelem.tag in DAQChanDescr.inttags:
                            DAQChanDescr.tags[subelem.tag] =  int(subelem.text)
                        elif subelem.tag in DAQChanDescr.floattags:
                            DAQChanDescr.tags[subelem.tag] =  float(subelem.text)
                        else:
                            DAQChanDescr.tags[subelem.tag] =  subelem.text
            
                if  subelem.tag in DAQChanDescr.internaltags:                              # checking for DIM or BIT
                    DAQChanDescr.clean_dimtags()
                    DAQChanDescr.clean_bittags()
                    index = subelem.text.strip()                                           # DIM or BIT index

                    for inelem in subelem:
                        if inelem.tag in DAQChanDescr.dimtags:
                        #print(inelem.tag, " " , type(inelem.text), " ", inelem.text)
                            if inelem.text != None and inelem.text != 'None':
                                if inelem.tag in DAQChanDescr.inttags:
                                    DAQChanDescr.dimtags[inelem.tag] =  int(inelem.text.strip())
                                elif inelem.tag in DAQChanDescr.floattags:
                                    DAQChanDescr.dimtags[inelem.tag] =  float(inelem.text.strip())
                                else:
                                    if type(inelem.text) == 'str':
                                        DAQChanDescr.dimtags[inelem.tag] =  inelem.text.strip()
                                    else:
                                        DAQChanDescr.dimtags[inelem.tag] =  inelem.text
                            elif  inelem.tag in DAQChanDescr.bittags:
                                if inelem.tag in DAQChanDescr.inttags:
                                    DAQChanDescr.bittags[inelem.tag] =  int(inelem.text.strip())
                                elif inelem.tag in DAQChanDescr.floattags:
                                    DAQChanDescr.bittags[inelem.tag] =  float(inelem.text.strip())
                                else:
                                    if type(inelem.text) == 'str':
                                        DAQChanDescr.bittags[inelem.tag] =  inelem.text.strip()
                                    else:
                                        DAQChanDescr.bittags[inelem.tag] =  inelem.text
                    item = {}            
                    if  subelem.tag == 'DIM':
                        #print('-------->', subelem.tag + index)
                        item[subelem.tag+index] = DAQChanDescr.dimtags
                        #print(item[subelem.tag+index])
                        DAQChanDescr.tags.setdefault(subelem.tag,{})
                        DAQChanDescr.tags[subelem.tag].update(item)
                        #print(DAQChanDescr.tags)
                        dims += 1
                    elif  subelem.tag == 'BIT':
                        item[subelem.tag+index] = DAQChanDescr.bittags
                        DAQChanDescr.tags.setdefault(subelem.tag,{})
                        DAQChanDescr.tags[subelem.tag].update(item)
                        bits += 1
        if  DAQChanDescr.tags['NAME'] != '':
        #creating a new chan description
        #tags['DIM'] = dims
        #tags['BIT'] = bits     
            if dims:
                DAQChanDescr.tags['DIM'].update({'DIMS':dims})
            if bits:
                DAQChanDescr.tags['BIT'].update({'BITS':bits})
            dims = 0
            bits = 0
            chd = DAQChanDescr.DAQChanDescr(chan = DAQChanDescr.tags)
            if self.chans == [] or chd.get_name() in self.chans:
                self.chandescrlst.append(chd)
    
    def GetDescriptionList(self, chans = []):
        if chans == []:
            return self.chandescrlst
        else :
            out = []
            for entry in self.chandescrlst:
                for ch in chans:
                    if re.search(ch, entry.get_name()):
                        out.append(entry)
        return out
         
    def GetDescriptionListAsXML(self, chans = []):
        res = self.GetDescriptionList(chans = [])
        out = '<?xml version="1.0" encoding="ISO-8859-1" ?>\n'
        out += DAQChanDescr.get_xml_tagn('CHANDESCRIPTIONS')
        out += DAQChanDescr.get_xml_tag('isodate')
        out += datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        out += DAQChanDescr.get_xml_endtagn('isodate')
        for d in res:
                out += d.get_xml_description()
        out += DAQChanDescr.get_xml_endtagn('CHANDESCRIPTIONS')
        return out