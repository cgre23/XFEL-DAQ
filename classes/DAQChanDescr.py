# channel description class

# Dimentions list should look like:
# [{'DIMn:'{'DIM_NAME':'',  'DIM_UNITS':'', 'DIM_DESCR':'', 'DIM_START':'', 'DIM_INC':'', 'DIM_NDATA':'', 'DIM_GROUPS':'', 'DIM_GROUP_INC':''}}, ...]
# where n - dimention index (0...)

# Bits list should look like:
# [{'BITn:'{'BIT_NAME':'',  'BIT_DESCR':''}}, ...]
# where n - bit index (0...)
# variable for XML channel description file parsing

tags = {'STREAM':0,  'EVTYPE':'', 'DTYPE':'', 'COUNT':0, 'SB_NAME':'None', 'DB_KEY':0, 'PROP':'', 'NAME':'', 'SETPOINT':0, 'SUBSYSTEM':'', 'UNITS':'', 'DESC':'', 'SIZE':0, 'DIM':{}, 'BIT':{}}
tagstoattr = { 'EVTYPE': 'EventTypeMask', 'DTYPE':'DAQdatatype', 'DB_KEY':'RCDBkey',  'SB_NAME':'ServerBlockName', 'PROP':'DOOCSproperty', 'NAME':'DAQchannel', 'SETPOINT':'Setpoint', 'SUBSYSTEM':'Subsystem', 'UNITS':'Units', 'DESC':'Description'}
tagstoattrsubch = {'DIM':{'DIM_NAME':'SubchannelName',  'DIM_UNITS':'SubchanelUnits', 'DIM_DESCR':'SubchannelDescription'}, 'BIT':{'BIT_NAME':'BitName',  'BIT_DESCR':'BitDescription'}}
internaltags = {'DIM', 'BIT'}
dimtags = {'DIM_NAME':None,  'DIM_UNITS':None, 'DIM_DESCR':None, 'DIM_START':None, 'DIM_INC':None, 'DIM_NDATA':None , 'DIM_GROUPS':None, 'DIM_GROUP_INC':None, 'DIM_XSTART':None,  'DIM_WIDTH':None,  'DIM_XBIN':None,  'DIM_YSTART':None, 'DIM_HEIGHT':None,  'DIM_YBIN':None, 'DIM_BPP':None, 'DIM_EBITPP':None, 'DIM_UNSIGNED':None}

# table for mapping TAGS to attributes

dimtagstoattr ={'DIM_UNITS':'Units', 'DIM_DESCR':'Description', 'DIM_START':'Start', 'DIM_INC':'Inc', 'DIM_NDATA':'GroupSamples', 'DIM_GROUPS':'Groups', 'DIM_GROUP_INC':'GroupInc', 'DIM_XSTART':'Xstart',  'DIM_WIDTH':'Width',  'DIM_XBIN':'Xbin',  'DIM_YSTART':'Ystart', 'DIM_HEIGHT':'Height',  'DIM_YBIN':'Ybin', 'DIM_BPP':'Bytesperpixel', 'DIM_EBITPP':'Bitsperpixel', 'DIM_UNSIGNED':'Unsigned'}

# Tags that can have sub-tags
bittags = {'BIT_NAME':'',  'BIT_DESCR':''}

# tags containig integers
inttags = ['STREAM',  'DB_KEY', 'COUNT', 'SETPOINT', 'SIZE', 'DIM_NDATA', 'DIM_GROUPS', 'DIM_XSTART', 'DIM_WIDTH', 'DIM_XBIN', 'DIM_YSTART', 'DIM_HEIGHT',  'DIM_YBIN', 'DIM_BPP', 'DIM_EBITPP', 'DIM_UNSIGNED'] 

# tags containig floats
floattags = ['DIM_START', 'DIM_INC', 'DIM_GROUP_INC']

def clean_dimtags():
    global dimtags
    dimtags = {'DIM_NAME':None,  'DIM_UNITS':None, 'DIM_DESCR':None, 'DIM_START':None, 'DIM_INC':None, 'DIM_NDATA':None , 'DIM_GROUPS':None, 'DIM_GROUP_INC':None, 'DIM_XSTART':None,  'DIM_WIDTH':None,  'DIM_XBIN':None,  'DIM_YSTART':None, 'DIM_HEIGHT':None,  'DIM_YBIN':None, 'DIM_BPP':None, 'DIM_EBITPP':None, 'DIM_UNSIGNED':None}
    
def clean_bittags():
    global bittags
    bittags = {'BIT_NAME':'',  'BIT_DESCR':''}

def allcleanup():
    global tags
    tags = {'STREAM':0,  'EVTYPE':'', 'DTYPE':'', 'COUNT':0, 'SB_NAME':'None', 'DB_KEY':0, 'PROP':'', 'NAME':'', 'SETPOINT':0, 'SUBSYSTEM':'', 'UNITS':'', 'DESC':'', 'SIZE':0, 'DIM':{}, 'BIT':{}}
    clean_dimtags()
    clean_bittags()


def get_xml_tag(pat):
    return '<'+pat+'>'
def get_xml_tagn(pat):
    return '<'+pat+'>\n'

def get_xml_endtag(pat):
    return '</'+pat+'>'
def get_xml_endtagn(pat):
    return '</'+pat+'>\n'

class  DAQChanDescr:
    
    def __init__(self, dtype = 0, sb_name = "", prop = "", name = "", chan={}):
        self.chan =   {'STREAM':0,  'EVTYPE':'', 'DTYPE':'', 'DB_KEY':0, 'COUNT':0, 'SB_NAME':'None', 'PROP':'', 'NAME':'', 'SETPOINT':0, 'SUBSYSTEM':'', 'UNITS':'', 'DESC':'', 'SIZE':0, 'DIM':{}, 'BIT':{}}
        if chan != {}:
            for key in chan.keys():
                if key in self.chan:
                    self.chan[key] = chan[key]
        if     sb_name != '':
            self.chan['SB_NAME'] = sb_name
        if     prop != '':
            self.chan['PROP'] = prop
        if     name != '':    
            self.chan['NAME'] = name
    def get_attr(self, nm):
            if nm in self.chan.keys():
                return self.chan[nm]
            else:
                return None

    def is_it_you(self, nm):
        if self.chan['NAME'] == nm:
            return True
        return False

    def get_dims(self, index):
        tag = "DIM"+str(index)
        #print(index, self.chan)
        for hash in  self.chan["DIM"]:
            #print('index', index,'tag', tag, 'hash',hash)
            if tag in hash:
                return self.chan["DIM"][hash]
                #return hash[tag]
        return None
            
    def get_bits(self, index):
        tag = "BIT"+str(index)
        for hash in  self.chan["BIT"]:
            if tag in hash:
                return hash[tag]
        return None
    
    def get_name(self):
        return self.chan['NAME']
        
    def print(self):
        print(self.chan)

    def get_xml_description(self):
        out = get_xml_tagn('CHANNEL')
        for key in self.chan.keys():
            if key == 'DIM' or key == 'BIT':
                if self.chan[key] != {}:
                    if key == 'DIM': 
                        n = self.chan[key]['DIMS']
                    else: n = self.chan[key]['BITS']
                    total = 0
                    index = 0
                    while total < n and index < 64:
                        lkey = key + str(index)
                        if lkey in  self.chan[key]:
                            out += get_xml_tag(key) + str(index) + '\n'
                            lkey = key + str(index)
                            for dkey in self.chan[key][lkey]:
                                if dkey != 'DIMS' and dkey != 'BITS':
                                    out += get_xml_tag(dkey)
                                    if self.chan[key][lkey][dkey] != None: out += str(self.chan[key][lkey][dkey]) #.replace('\n', '')
                                    out += get_xml_endtagn(dkey)
                            out += get_xml_endtagn(key)
                            total += 1
                        index += 1
            else:
                out += get_xml_tag(key) 
                if self.chan[key] == 0 or self.chan[key] == '' and key!='DESC' and key!='UNITS':
                    out += str(0)
                elif self.chan[key] == 0 or self.chan[key] == '' and (key == 'DESC' or key == 'UNITS'):
                    out += '' 
                elif self.chan[key] == 'None':
                    out += ''
                else:
                    out += str(self.chan[key])
                out += get_xml_endtagn(key)
        out += get_xml_endtagn('CHANNEL')
        return out 
    '''
        <CHANNEL>
<STREAM>0</STREAM>
<EVTYPE>0</EVTYPE>
<DTYPE>0</DTYPE>
<COUNT>0</COUNT>
<SB_NAME></SB_NAME>

<DB_KEY>138375</DB_KEY>
<PROP>FLASH.DIAG/BPM/11FLFMAFF/DAQ_CHANNEL</PROP>
<NAME>FLASH.DIAG/BPM/11FLFMAFF</NAME>
<SETPOINT>0</SETPOINT>
<SUBSYSTEM>FLASH_BPM_DIAGNOSTICS</SUBSYSTEM>
<UNITS>mm</UNITS>
<DESC></DESC>
<SIZE>2048</SIZE>
<DIM>0
<DIM_NAME>X.TD</DIM_NAME>
<DIM_UNITS>mm</DIM_UNITS>
<DIM_DESCR>FLASH BPM X</DIM_DESCR>
</DIM>
<DIM>1
<DIM_NAME>Y.TD</DIM_NAME>
<DIM_UNITS>mm</DIM_UNITS>
<DIM_DESCR>FLASH BPM Y</DIM_DESCR>
</DIM>
<BIT>0
<BIT_NAME>OpMode: GUN</BIT_NAME>
<BIT_DESCR>GUN operation mode</BIT_DESCR>
</BIT>
<BIT>1
<BIT_NAME>OpMode: ANALYSIS</BIT_NAME>
<BIT_DESCR>ANALYSIS operation mode</BIT_DESCR>
</BIT>

</CHANNEL>
'''