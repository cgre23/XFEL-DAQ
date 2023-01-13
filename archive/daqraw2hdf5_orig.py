import sys
import os

import pydaq
import pydoocs
import time


import pandas as pd
import numpy as np
import h5py as h5


from datetime import datetime
from datetime import timedelta

scriptpath = "../"

# Add the directory containing your module to the Python path (wants absolute paths)
sys.path.append(os.path.abspath(scriptpath))

import classes.DAQChanDescrList as DAQChanDescrList
import classes.DAQChanDescr as DAQChanDescr
import classes.DAQRequest as DAQRequest
import classes.DAQbasic as DAQbasic

#tagstoattr = { 'EVTYPE': 'EventTypeMask', 'DTYPE':'DAQdatatype', 'DB_KEY':'RCDBkey',  'SB_NAME':'ServerBlockName', 'PROP':'DOOCSproperty', 'NAME':'DAQchannel', 'SETPOINT':'Setpoint', 'SUBSYSTEM':'Subsystem', 'UNITS':'Units', 'DESC':'Description'}
#tagsfunc = {'EVTYPE': [ get_daqname, daqeventtypes ] , 'DTYPE': [ get_daqname, daqdatatypes ] }   # table for converting some parameters via dictionaries

image_params = ['width', 'height', 'aoi_width', 'aoi_height', 'x_start', 'y_start', 'hbin', 'vbin', 'bpp', 'ebitpp']
chandescrlst = []     # all channel descriptions

#print(pydoocs.__file__)
#print(pydaq.__file__)

def find_or_create_stat(daqname, macropulse, timestampsec, timestampusec, subchan, dtype, stats_list):
    #creating/finding the entry
    curentry = None
    for stats in stats_list:
        if stats['daqname'] == daqname:
            curentry = stats
            break
    if curentry == None:
            curentry = {}
            curentry['daqname'] = daqname
            curentry['events'] = 0
            curentry['subch'] = subchan
            curentry['type'] = dtype
            curentry['data'] = []
            curentry['EventID'] = []
            curentry['TimeStamp'] = []
            stats_list.append(curentry)
    # filling fevent
    curentry['events'] += 1
    curentry['EventID'].append(macropulse)
    curentry['TimeStamp'].append([timestampsec, timestampusec])
    return curentry

def HelpAndExit():
    print("%s: help:\n\n" % (os.path.basename(sys.argv[0])))
    print("The program converts FLASH/XFEL DAQ data raw files  into HDF5 \n")
    print("%s -xml xmlfile [-start stime -stop stime -descr descr_file -dout path -xfel -local -h -print] \n" % (os.path.basename(sys.argv[0])))
    print("\t-xml file\t- XML file with DAQ request parameters \n")
    print("\t-start stime\t- stime is the start time to be used in the request (overwrites XML start time). The format (Year-Month-DayTHour:Min:Sec, eg. 2020-01-01T00:00:00)  \n")
    print("\t-stop stime\t- stime is the stop time to be used in the request (overwrites XML start time). The format (Year-Month-DayTHour:Min:Sec, eg. 2020-01-01T00:00:00)  \n")
    print("\t-descr file\t- XML file with DAQ channel descriptions (if not set - default one will be used depending on linac) \n")
    print("\t-dout path\t- directory for storing  HDF5 files  (if not set - the current directory will be used \n")
    print("\t-xfel \t\t- data for XFEL (default FLASH) \n")
    print("\t-local \t\t- DAQ data extraction local mode will be used (default DAQ data service)\n")
    print("\t-print \t\t- print data\n")
    print("\t-h\t\t- prints this help\n")
    sys.exit(1)

def Fatal(msg):
    sys.stderr.write("%s: %s\n\n" % (os.path.basename(sys.argv[0]), msg))
    HelpAndExit()

def NextArg(i):
    '''Return the next command line argument (if there is one)'''
    if ((i+1) >= len(sys.argv)):
        Fatal("'%s' expected an argument" % sys.argv[i])
    return(1, sys.argv[i+1])

snch = ''
image = False
stats_list = []   # list of dictionaries [ {'daqname': {'subch':# data':[] 'EventID':[] 'TimeStamp':[]} {} ]

if __name__=='__main__':

    xmlfile = None
    xmldfile = None
    do_print = False
    xfel = False
    localmode = False
    starttime = None
    stoptime = None
    dout = None
    # Parse command line
    skip = 0
    for i in range(1, len(sys.argv)):
        if not skip:
            if sys.argv[i][:4] == "-xml": (skip,xmlfile)  = NextArg(i)
            elif sys.argv[i][:6] == "-start": (skip,starttime)  = NextArg(i)
            elif sys.argv[i][:5] == "-stop": (skip,stoptime)  = NextArg(i)
            elif sys.argv[i][:6] == "-descr": (skip,xmldfile)  = NextArg(i)
            elif sys.argv[i][:5] == "-dout": (skip,dout)  = NextArg(i)
            elif sys.argv[i][:5] == "-xfel": xfel = True
            elif sys.argv[i][:6] == "-local": localmode = True
            elif sys.argv[i][:6] == "-print": do_print = True
            elif sys.argv[i][:2] == "-h": HelpAndExit()
            elif sys.argv[i][:1] == "-":  Fatal("'%s' unknown argument" % sys.argv[i])
            else:                         Fatal("'%s' unexpected" % sys.argv[i])
        else: skip = 0
    timeofstart = datetime.now()
    if not xmlfile:
        Fatal("Please, check you input arguments")

    #=========================XML request========================================
    if (not os.path.exists(xmlfile)) or (not os.access(xmlfile, os.R_OK)):
        Fatal("XML request file '%s' doesn't exist or not readable" % xmlfile)
    #=========================XML description========================================
    linac = 'FLASH'
    #print(xfel)
    if not xmldfile:
        if not xfel:
            xmldfile = DAQbasic.daqdescrfile[0]
        else:
            xmldfile = DAQbasic.daqdescrfile[1]
            linac = 'XFEL'

    if (not os.path.exists(xmldfile)) or (not os.access(xmldfile, os.R_OK)):
        Fatal("XML description file '%s' doesn't exist or not readable" % xmldfile)
    #=========================Data out path========================================
    if not dout:
        dout = './'
    if (not os.path.exists(dout)) or (not os.access(dout, os.W_OK)):
        Fatal("Directory for  HDF5 files '%s' doesn't exist or not writable" % dout)

    if not  dout.endswith('/'):
        dout += '/'

    request = DAQRequest.DAQRequest(xmlfile = xmlfile)
    reqchans = request.getChans()
    if not reqchans:
        reqchans = []
    else:
        res = [ sub['name'] for sub in  reqchans]
        reqchans = res

    if starttime:
        if request.setStartTime(starttime):
            Fatal("Please, check start time format '%s'. It must be 'Year-Month-DayTHour:Min:Sec' " % starttime)

    if stoptime:
        if request.setStopTime(stoptime):
            Fatal("Please, check stop time format '%s'. It must be 'Year-Month-DayTHour:Min:Sec' " % starttime)

    # saving the updated XML request file
    tmpxmlfile = '/tmp/' + str(os.getpid()) +  '.xml'
    xml, res = request.create_xml(tmpxmlfile)

    if not res:
        print('Failed to create XML file %s ... exiting'%tmpxmlfile)
        sys.exit(-1)
    else:
        if do_print:
            print('Final request')
            print(xml)


    #print(reqchans)
    #print(xmldfile)
    chandescrlst = DAQChanDescrList.ChanDescrList(xmlfile=xmldfile, chans = reqchans).GetDescriptionList()




    daqfiles, daqchannels = DAQbasic.get_channel_file_list(tmpxmlfile, linac, localmode, True, do_print)
    os.remove(tmpxmlfile)
    localxmlfile = tmpxmlfile

    if daqfiles == []:
        print('No files found... exiting')
        sys.exit(-2)
    # we extract only requested channels
    if reqchans:
            daqchannels = reqchans
    xml_basic = DAQbasic.prepare_basic_request(request.getExp(), daqchannels, request.getScanMode())
    for file in daqfiles:
        stats_list = []
        xml_request = DAQbasic.prepare_file_request(xml_basic, file)
        #print(xml_request)
        with open(localxmlfile, 'w') as writer:
            writer.write(xml_request)

        daqfiles, daqchannels = DAQbasic.get_channel_file_list(localxmlfile, linac, localmode, True, do_print)
        if reqchans:
            daqchannels = reqchans
        daqchannels.sort()
        print("Working with %d channels\n" %  len(daqchannels))
        #sys.exit(0)
        try:
            err = pydaq.connect(xml=localxmlfile, linac=linac, local=localmode, cachesize=10000)
        except pydaq.PyDaqException as err:
            print('Something wrong with connect... exiting')
            print(err)
            os.remove(localxmlfile)
            sys.exit(-1)


        stop = False
        emptycount = 0
        total = 0
        print('reading    from  %s . . . '%(file), end = '', flush=True)
        oncedata = True
        while not stop and (emptycount < 100000):
            try:
                channels = pydaq.getdata()

                if channels == []:
                    emptycount += 1
                    time.sleep(0.001)
                    continue
                if channels == None:
                    break

                #print(channels)
                nch = 0
                once = True
                once2 = True
                if isinstance(channels[0], dict): # slow channels
                    daqnameold = None
                    curentry = None
                    for entry in channels:
                        daqname = entry['miscellaneous']['daqname']
                        timestampsec = int(entry['timestamp']//1)
                        timestampusec = int((entry['timestamp'] % 1)*1000000)
                        subchan = len(entry['data'])
                        curentry = find_or_create_stat(daqname, entry['macropulse'], timestampsec, timestampusec, subchan, 'DATA_FLOAT', stats_list)
                        data = entry['data']
                        chtotal = curentry['events']
                        # filling the data
                        for subi in range(0, subchan):
                            sub = data[subi]
                            dt = sub[1]
                            curentry['data'].append(dt)

                    # checking total number of evetns (max)
                    totalmax = 0
                    for stats in stats_list:
                        if totalmax < stats['events']:
                            totalmax = stats['events']
                    total += totalmax
                    continue
                total += 1
                for chan in channels:
                    if do_print:
                        print(chan)
                    subchan = len(chan)
                    daqname = chan[0]['miscellaneous']['daqname']
                    timestampsec = int(chan[0]['timestamp']//1)
                    timestampusec = int((chan[0]['timestamp'] % 1)*1000000)
                    macropulse =  chan[0]['macropulse']
                    dtype = chan[0]['type']
                    curentry = find_or_create_stat(daqname, macropulse, timestampsec, timestampusec, subchan, dtype, stats_list)
                    chtotal = curentry['events']
                    if daqname:
                        for subi in range(0, subchan):
                            sub = chan[subi]
                            if 'data' in sub:
                                data = sub['data']
                                if isinstance(data, list):
                                    if data != []:
                                        data = sub['data'][subi][1]
                                        curentry['data'].append(data)
                                    else:
                                        curentry['data'].append([])
                                elif 'index' in sub['miscellaneous']:
                                    curentry['data'].append(sub['data'][:,1])
                                else:
                                    #print("This is an IMAGE %dx%d"%(len(data[0]), len(data)))
                                    image = True
                                    curentry['data'].append(sub['data'])
                                #print(curentry)

                    #sys.exit(0)
                emptycount = 0
                if do_print and not total % 100:
                    print("\r%d  channels:%d" % (total, len(channels)), end=" ")
            except pydoocs.PyDoocsException as err:
                print('pydoocsException (%s)!!! total events: %d ... exiting'%(err, total))
                pydaq.disconnect()
                sys.exit(-1)
            except Exception as err:
                print('Something wrong ... stopping %s' % str(err))
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                stop = True
            except pydaq.PyDaqException as err:
                print('pydaqException (%s)!!! total events: %d ... exiting'%(err, total))
                pydaq.disconnect()
                sys.exit(-1)

        pydaq.disconnect()
        if do_print:
            print('\nTotal events: %d emptycount %d\n\n' % (total, emptycount))

        #for entry in stats_list:
        #    print(entry)
        if do_print:
            for stats in stats_list:
                print(stats)
                #print(stats['daqname'], ':\t', stats['events'], ' events')
        print('done (total events: %d)'%(total))
    # writing to HDF5 file
        now = datetime.now()
        timestamp = now.strftime('%Y-%m-%dT%H:%M:%S') + ('-%02d' % (now.microsecond / 10000))

        parts = file.split('/')
        fname = parts[len(parts) -1].split('.')[0]

        hd5file = dout + fname + '.hdf5'
        print('converting into %s . . . '%(hd5file), end = '', flush=True)
        fd = h5.File(hd5file, "w")
        # point to the default data to be plotted
        fd.attrs[u'default'] = u'entry'
        # give the HDF5 root some more attributes
        fd.attrs[u'file_name'] = hd5file
        fd.attrs[u'file_time'] = timestamp
        fd.attrs[u'input_file'] = file
        fd.attrs[u'creator'] = os.path.basename(sys.argv[0])
        fd.attrs[u'HDF5_Version'] = h5.version.hdf5_version
        fd.attrs[u'h5py_version'] = h5.version.version

        inttype = False
        groupnum = 0

        for daqchan in daqchannels:
            found = False
            for stats in stats_list:
                if stats['daqname'] == daqchan:
                    found = True
                    break
            if not found:
                print("%s NOT FOUND"%daqchan)
                continue;
            groupnum += 1
            sub = 0
            #print(stats['daqname'], stats['subch'], stats['type'], type(stats['data'][0]))
            #continue
            subch = stats['subch']
            chd = DAQbasic.getdescr(stats['daqname'], chandescrlst)      # find our channel description
            #print(chd.get_dims(0))
            #print('Check for:', stats['daqname'])
            #if chd: print('In:', chd.chan)
            while sub < subch:
                #print(stats['daqname'],  ": ", sub, stats['type'])
                if stats['type'] == 'DATA_FLOAT':
                    mchan = stats['data']
                elif stats['type'] == 'A_USTR':
                    mchan = list(stats['data'])
                elif stats['type'] == 'A_TS_GSPECTRUM' or stats['type'] == 'A_TS_SPECTRUM':
                    data = stats['data'][sub::subch]
                    mchan = []
                    kk = 0
                    while kk < len(data):
                        dt = data[kk]
                        if isinstance(dt, list):
                            if len(dt) != 0:
                                #mchan.append(dt[:, [1]])
                                mchan.append(dt)
                        elif isinstance(dt, np.ndarray):
                                mchan.append(dt.tolist())
                        kk += 1
                elif stats['type'] == 'IMAGE':
                    #print("Image is not yet implemented")
                    #print(stats['data'])
                    mchan = list(stats['data'])
                    #sub += 1
                    #continue
                if stats['type'] == 'A_TS_GSPECTRUM' or  stats['type'] == 'A_TS_SPECTRUM':
                    mm = 0
                    maxlen = 0
                    difflength = False
                    #print(type(mchan[mm]))
                    for mm in range(0,len(mchan)):
                        if maxlen != 0 and maxlen != len(mchan[mm]):
                            difflength = True
                        if maxlen < len(mchan[mm]):
                            maxlen = len(mchan[mm])

                    if difflength:                                    # we have to do something to solve different length problem
                        sz = len(mchan)
                        nn = 0
                        #print('  ',sz)
                        result = []
                        for nn in range(0,sz):
                            if len(mchan[nn]) < maxlen:
                                diff = maxlen - len(mchan[nn])
                                mchan[nn] = np.append (mchan[nn], [0]*diff)
                                result.append(mchan[nn])
                        mchan = result
                #print(mchan)

                datatocheck = None
                if (stats['type'] == 'IMAGE'): # and isinstance(mchan[0], np.ndarray) and  isinstance(mchan[0][0], np.ndarray):
                     datatocheck =   mchan[0][0][0]
                darray = np.array(mchan)
                # we have array for all train Ids
                #print("Type: ", type(mchan), ",\n", darray)
                #print("Size: ", darray.shape, ",\n", darray)

                groupname = "/" + stats['daqname']  # group name for a channel

                if sub == 0:
                    # creating group for a channel
                    # print('GROUP[%d]:'%(groupnum), groupname)
                    group = fd.create_group(groupname)
                    dataset = group.create_dataset(
                        "TrainId", dtype="uint64", data=stats['EventID'], compression='gzip')  # creating TrainID dataset
                    # creating TimeStamp dataset
                    timest = group.create_dataset(
                        "TimeStamp", dtype="uint64", data=stats['TimeStamp'], compression='gzip')
                    # creating common attributes
                    if chd != None:
                        for attr in DAQChanDescr.tagstoattr.keys():
                            if chd.get_attr(attr) != None:
                                if attr in DAQbasic.tagsfunc:
                                    lst = DAQbasic.tagsfunc[attr]
                                    #tp, mr =  tagsfunc[attr](chd.get_attr(attr), daqdatatypes)
                                    tp, mr = lst[0](chd.get_attr(attr), lst[1])
                                    group.attrs[DAQChanDescr.tagstoattr[attr]] = tp + ' (' + mr + ')'
                                else:
                                    group.attrs[DAQChanDescr.tagstoattr[attr]] = chd.get_attr(attr)

                # finding out the subchannel name from the description
                #print("checking subch: ", sub)
                #print('In:', chd)
                if chd:
                    dm = chd.get_dims(sub)
                else: dm = None
                #print(dm)
                #print(chd.get_name())
                if dm == None:
                    if subch > 1:
                        subchname = "Subchan:" + str(sub)
                    else:
                        subchname = "Value"
                else:
                    subchname = dm['DIM_NAME']
                    # creating all datasets and filling them
                if subchname == 'Float':
                    subchname = "Value"
                tp = 'unknown'
                if inttype:
                    if dm != None and 'DIM_EBITPP' in dm and dm['DIM_EBITPP'] != None:
                        if 'DIM_UNSIGNED' in dm and dm['DIM_UNSIGNED'] != None and dm['DIM_UNSIGNED']:
                            uns = True
                        else:
                            uns = False
                        tp = DAQbasic.bits_to_inttype(int(dm['DIM_EBITPP']), bool(uns))
                    if tp == 'unknown':
                        # creating data set for values as integers
                        data = group.create_dataset(
                            subchname, dtype="int64", data=darray, compression='gzip', compression_opts=1)
                    else:
                        # creating data set for values as type from description
                        data = group.create_dataset(
                            subchname, dtype=tp, data=darray, compression='gzip', compression_opts=1)
                else:
                    # creating data set for values as float
                    if stats['type'] == 'IMAGE':
                        #print("Here", type(datatocheck))
                        if isinstance(datatocheck, np.uint16):
                            data = group.create_dataset(
                            subchname, dtype="uint16", data=darray, compression='gzip', compression_opts=1)
                        elif isinstance(datatocheck, np.uint8):
                            data = group.create_dataset(
                            subchname, dtype="uint8", data=darray, compression='gzip', compression_opts=1)
                        else:
                            print(stats['daqname'], 'Unsupported data type for image:', type(datatocheck))
                    else:
                        #print(subchname)
                        #print(darray)
                        data = group.create_dataset(
                            subchname, dtype="float32", data=darray, compression='gzip', compression_opts=1)

                if dm != None:
                    #print(dm)
                    for attr in DAQChanDescr.dimtagstoattr.keys():
                        #print(attr)
                        if dm[attr] != None:
                            data.attrs[DAQChanDescr.dimtagstoattr[attr]] = dm[attr]
                     #   else:
                     #       data.attrs[dimtagstoattr[attr]] = "None"

                fd.flush()
                sub += 1                                    # next subchannel
        fd.close()
        print('done\n')
        os.remove(localxmlfile)
    print("All is done. Elapsed time  %s\n"%(str(datetime.now() - timeofstart)))
