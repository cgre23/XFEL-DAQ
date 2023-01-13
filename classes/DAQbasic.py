import sys
from struct import pack, unpack
import pydaq


def float2int(a):
    fmt = '>f'
    b = pack(fmt, a)
    return int.from_bytes(b, 'big')


def bits_to_inttype(bits, unsign):
    tp = 'unknown'
#    print('bits_to_inttype', isinstance( bits, str ), isinstance( unsign,  bool))
    if isinstance(bits, int) and isinstance(unsign,  bool):
        dl = 0

        if not unsign:
            dl = 1
        if bits <= 8 - dl:
            tp = 'int8'
        elif bits <= 16 - dl:
            tp = 'int16'
        elif bits <= 32 - dl:
            tp = 'int32'
        else:
            tp = 'int64'
        if tp != 'unknown' and unsign:
            tp = 'u' + tp
    return tp

#DAQ event types


daqeventtypes = {
    '0': 'HB',                 # heart beat event
    '1': 'NORMAL',             # normal event
    '2': 'BOR',                # begin of run event
    '3': 'EOR',                # end of run event
    '4': 'ENV',                # environment (Slow Control) event
    '5': 'UPD',                # update event
    '6': 'IMAGE',              # image event
    '7': 'WS',                 # Wire scanner event
    '8': 'MCP',                # MCP event
    '9': 'WSS',                # WS server event
    '10': 'BL1',               # Beam line 1 server event
    '11': 'BL2',               # Beam line 2 server event
    '12': 'BL3=',               # Beam line 3 server event
    '13': 'PG0',               # PG0 server event
    '14': 'PG1',               # PG1 server event
    '15': 'PG2',               # PG2 server event
    '16': 'GMD',               # GMD event
    '17': 'PHOTEN',            # PHOTON ENERGY event
    '18': 'PHOTWL',            # PHOTON Wave Length
    '19': 'BEAM_ENERGY',       # all electron beam ENERGY related event
    '20': 'LLRF_ML',           # LLRF ML server event
    # all electron beam ENERGY related event (in BYPASS)
    '21': 'BEAM_ENERGY_BYPASS',
    '22': 'SPECTR_1',          # event for spectrometer 1
    '23': 'SPECTR_2',          # event for spectrometer 2
    '24': 'SPECTR_3',          # event for spectrometer 3
    '25': 'SPECTR_4',          # event for spectrometer 4
    '26': 'SPECTR_5',          # event for spectrometer 5
    '27': 'TOROID_ML',         # event for TOROID ML server
    '28': 'EV_28',                # event for TYPE 28
    '29': 'EV_29',                # event for TYPE 29
    '30': 'EV_30',                # event for TYPE 30
    '31': 'EV_31',                # event for TYPE 31
    '32': 'EV_EVMAX'              # let's see when we exeed this !!!
}

#DAQ data types

daqdatatypes = {
    '1': 'UPD_BLOCK',     # UPDate block type
    '2': 'ENV_DICT_BLOCK',        # Environment dictionary block type
    '3': 'ENV_BLOCK',                     # Environment block type
    '4': 'BOR_BLOCK',                     # Begin of run block (see format UPD)
    '5': 'EOR_BLOCK',                     # End of run block (see format UPD)
    # BPM with X and Y channels (2 ADC channels)
    '6': 'BLOCK_BPM',
    # BPM (Zeuthen Cavity, X, Y , I, Q -  4 ADC channels)
    '7': 'BLOCK_BPM_Z',
    '8': 'BLOCK_BPM_S',                # BPM (SACLAY Reentrant)
    '9': 'BLOCK_SINGLE',               # Single Channel
    '10': 'BLOCK_TOROID',            # Toroid ( for 2 channels)
    '11': 'BLOCK_RF_250K',           # RF with 250kHz Down Converted Input
    '12': 'BLOCK_ENERGY',           # Energy server block
    '13': 'BLOCK_IMAGE',               # Image block
    '14': 'BLOCK_WS_FAST',         # Wire scanner block, fast scan
    '15': 'BLOCK_WS_SLOW',        # Wire scanner block, slow scan
    '16': 'BLOCK_CPLINTL',           # Coupler Interlock
    '17': 'BLOCK_GUNINTL',          # GUN Interlock
    '18': 'BLOCK_MCP',                   # MCP
    '19': 'BLOCK_PHM',                   # Phase monitors
    '20': 'BLOCK_WSS_RAW',       # Wire scanner server raw data
    '21': 'BLOCK_WSS_COR',        # Wire scanner server corrected data
    '22': 'BLOCK_NAME_VALUE',  # generic NAME/VALUE (float) block
    '23': 'BLOCK_NAME_VALUE_STRING',  # generic NAME/VALUE (string) block
    '24': 'BLOCK_IMG_ROI1',        # image ROI parameters and statistics 1 channel
    '25': 'BLOCK_IMG_ROI2',        # image ROI parameters and statistics 2 channels
    '26': 'BLOCK_IMG_ROI3',        # image ROI parameters and statistics 3 channels
    '27': 'BLOCK_IMAGE_EXT',        # new (DOOCS defined) image format inside
    '28': 'BLOCK_GENERIC_SPECT',    # multi subchannel spectra with individual parameters

    # shouldn't be used beacuse 0x80000000 us used as the indicator for
    '31': 'TTF2_UPD_BLOCK_DONT_USE_31',
                                         # data types with code > 32

    '32': 'UPD_BLOCK_2010',               # UPDate block type
    '34': 'ENV_DICT_BLOCK_2010',         # Environment dictionary block type
    '35': 'ENV_BLOCK_2010',               # Environment block type
    '36': 'BOR_BLOCK_2010',               # Begin of run block (see format UPD)
    '37': 'EOR_BLOCK_2010',               # End of run block (see format UPD)
    # BPM with X and Y channels (2 ADC channels)
    '38': 'BLOCK_BPM_2010',
    # BPM (Zeuthen Cavity, X, Y , I, Q -  4 ADC channels)
    '39': 'BLOCK_BPM_Z_2010',
    '40': 'BLOCK_BPM_S_2010',          # BPM (SACLAY Reentrant)
    '41': 'BLOCK_1CHAN_2010',          # Single Channel
    '42': 'BLOCK_TOROID_2010',        # Toroid ( for 2 channels)
    '43': 'BLOCK_RF_250K_2010',       # RF with 250kHz Down Converted Input
    '44': 'BLOCK_ENERGY_2010',       # Energy server block
    '45': 'BLOCK_2CHAN_2010',          # 2 channels
    '46': 'BLOCK_WS_2010',                  # Wire scanner block
    '47': 'BLOCK_4CHAN_2010',          # 4 channels
    '48': 'BLOCK_CPLINTL_2010',       # Coupler Interlock
    '49': 'BLOCK_GUNINTL_2010',      # GUN Interlock
    '50': 'BLOCK_MCP_2010',               # MCP
    '51': 'BLOCK_PHM_2010',               # Phase monitors
    '52': 'BLOCK_6CHAN_2010',           # 6 channels
    '53': 'BLOCK_8CHAN_2010',           # 8 channels
    '60': 'BLOCK_3CHAN_2010',           # 3 channels
    '61': 'BLOCK_5CHAN_2010',           # 5 channels
    '62': 'BLOCK_7CHAN_2010',           # 7 channels
    '63': 'BLOCK_MAX_2010=63'
}


def get_daqname(sbits, indict):
    tp = 'unknown'
    if isinstance(sbits, str) and isinstance(indict, dict):
        bits = int(sbits)
        if bits < 0:
            bits = bits & 0xffffffff
        sh = 0
        if bits & 0x80000000:
            sh = 32
        i = 0
        found = -1
        while i < 32:
            if bits & 1 << i:
                key = str(i + sh)
                if key in indict:
                    tp = indict[key]
                    found = i
                    break
            i += 1
    return tp,  str(found + sh)


tagsfunc = {'EVTYPE': [get_daqname, daqeventtypes], 'DTYPE': [
    get_daqname, daqdatatypes]}   # table for converting some parameters via dictionaries
daqdescrfile = ['/daq/ttf2/adm/daq_channel_descriptions.xml',
                '/daq/xfel/adm/daq_channel_descriptions.xml']
linacname = ['FLASH', 'XFEL']


def getdescr(name, chandescrlst):
    for descr in chandescrlst:
        if descr.is_it_you(name):
            return descr
    return None


def prepare_basic_request(exp, daqchannels, scanmode):
    out = "<DAQREQ>\n<Exp  name='"
    out += exp
    out += "'/>\n"
    for chan in daqchannels:
        out += "<Chan name='"
        out += chan
        out += "'/>\n"
    if scanmode:
        out += "<ScanMode mode='"
        out += str(scanmode)
        out += "'/>\n"
    return out


def prepare_file_request(xml_basic, file):
    out = xml_basic
    out += "<File name='"
    out += file
    out += "'/>\n"
    out += "</DAQREQ>\n"
    return out


def get_channel_file_list(xmlfile, linac, localmode, onlywithevents, debug):
    if not xmlfile or not linac:
        print('get_channel_file_list: please check your parameters tmpxmlfile:',
              xmlfile, 'linac', linac, 'localmode', localmode)
        print('get_channel_file_list: exiting ...')
        sys.exit(-1)

    try:
        err = pydaq.connect(xml=xmlfile, linac=linac,
                            local=localmode, mode='list', filelist=True)
    except pydaq.PyDaqException as err:
        print('Something wrong with connect... exiting')
        print(err)
        sys.exit(-1)

    daqchannels = []
    daqfiles = []
    #print(err)
    if err != []:
        i = 0
        j = 0
        if debug:
            print('--------- CHANNELS ----------')
        for entry in err:
            if 'files' in entry:
                daqfiles = entry['files']
                if debug:
                    print('--------- FILES ----------')
                    for file in entry['files']:
                        print('[%d] ' % (j), file)
                        j += 1
            else:
                if not onlywithevents or (onlywithevents and (entry['events'] > 0)):
                    daqchannels.append(entry['daqname'])
                    if debug:
                        print('[%d] %s events:%d subchannels:%d' % (
                            i, entry['daqname'], entry['events'], len(entry['miscellaneous'])))
                        for sub in entry['miscellaneous']:
                            print("\tindex:%d name:%s units:%s descr:%s" % (
                                sub['dim'], sub['name'], sub['units'], sub['description']))
                i += 1
        #if do_print: sys.exit(0)

    pydaq.disconnect()
    return daqfiles, daqchannels
