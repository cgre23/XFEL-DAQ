import sys
import os

import pydaq
import pydoocs
import time
import pickle

import numpy as np
import h5py as h5


from datetime import datetime
from datetime import timedelta
from classes.DAQBunchPattern import DAQBunchPattern

import collections

scriptpath = "../"

# Add the directory containing your module to the Python path (wants absolute paths)
sys.path.append(os.path.abspath(scriptpath))

import classes.DAQChanDescrList as DAQChanDescrList
import classes.DAQChanDescr as DAQChanDescr
import classes.DAQRequest as DAQRequest
import classes.DAQbasic as DAQbasic

image_params = ['width', 'height', 'aoi_width', 'aoi_height', 'x_start', 'y_start', 'hbin', 'vbin', 'bpp', 'ebitpp']
chandescrlst = []     # all channel descriptions
linac = 'XFEL'
logic = 'AND'
timing_channels={'FLASH':'TIMINGINFO/TIME1.BUNCH_PATTERN', 'XFEL':'XFEL.DIAG/TIMINGINFO/TIME1.BUNCH_PATTERN'}
#print(pydoocs.__file__)
#print(pydaq.__file__)
total_subchan_name_bad = 0
pickle_basic_name = 'mydata'


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

def getsize(o):
    """
    calculating the size of a dictionary of the following format
    {'daqname':name, 'events':n, 'subch':m, 'type':'DATA_xxx', 'data':[] 'EventID':[] 'TimeStamp':[]}
        return calculated size
    """
    if not isinstance(o, dict): return -1
    if o['daqname'] == 'XFEL.FEL/XGM/XGM.2643.T9':
        print(o['data'])
        print(sys.getsizeof(o))
        print(len(o['data']), sys.getsizeof(o['data']))
        print(len(o['EventID']), sys.getsizeof(o['EventID']))
        print(len(o['TimeStamp']),  sys.getsizeof(o['TimeStamp']))

    return  sys.getsizeof(o) + sys.getsizeof(o['data']) + sys.getsizeof(o['EventID']) + sys.getsizeof(o['TimeStamp'])

# function to return a list of paths to each dataset
def getdatasets(key,archive):

  if key[-1] != '/': key += '/'

  out = []

  for name in archive[key]:

    path = key + name

    if isinstance(archive[path], h5.Dataset):
      out += [path]
    else:
       out += getdatasets(path,archive)

  return out

def copy_files_to_one_file(input_files, output_file):
    # open HDF5-files
    with  h5.File(output_file,'w') as new_data:
        for inputfile in input_files:
            print(inputfile)
            data     = h5.File(inputfile,'r')
            # read as much datasets as possible from the old HDF5-file
            datasets = getdatasets('/',data)

            # get the group-names from the lists of datasets
            groups = list(set([i[::-1].split('/',1)[1][::-1] for i in datasets]))
            groups = [i for i in groups if len(i)>0]

            # sort groups based on depth
            idx    = np.argsort(np.array([len(i.split('/')) for i in groups]))
            groups = [groups[i] for i in idx]

            # create all groups that contain dataset that will be copied
            for group in groups:
                if not group in new_data.keys():
                    new_data.create_group(group)
                else:
                    print(group, " is already in the file")

            # copy datasets
            for path in datasets:
                # - get group name
                group = path[::-1].split('/',1)[1][::-1]
                # - minimum group name
                if len(group) == 0: group = '/'
                    # - copy data
                print(path)
                data.copy(path, new_data[group])


def write_data_hdf5_file(fd, stats,  chandescrlst):
    sub = 0
    global mchan
    inttype = False
    #print(stats['daqname'], stats['subch'], stats['type'], type(stats['data'][0]))
    #continue
    subch = stats['subch']
    # find our channel description
    chd = DAQbasic.getdescr(stats['daqname'], chandescrlst)
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
            #print(data)
            mchan = []
            kk = 0
            while kk < len(data):
                dt = data[kk]
                if isinstance(dt, list):
                    if len(dt) != 0:
                        #mchan.append(dt[:, [1]])
                        mchan.append(dt)
                    else:
                        mchan.append([np.nan])
                elif isinstance(dt, np.ndarray):
                        mchan.append(dt.tolist())
                kk += 1
        elif stats['type'] == 'IMAGE':
            #print("Image is not yet implemented")
            #print(stats['data'])
            mchan = list(stats['data'])
            #sub += 1
            #continue
        if stats['type'] == 'A_TS_GSPECTRUM' or stats['type'] == 'A_TS_SPECTRUM':
            mm = 0
            maxlen = 0
            difflength = False
            #print(type(mchan[mm]))
            for mm in range(0, len(mchan)):
                if maxlen != 0 and maxlen != len(mchan[mm]):
                    difflength = True
                if maxlen < len(mchan[mm]):
                    maxlen = len(mchan[mm])

            if difflength:                                    # we have to do something to solve different length problem
                sz = len(mchan)
                nn = 0
                #print('  ',sz)
                result = []
                for nn in range(0, sz):
                    if len(mchan[nn]) < maxlen:
                        diff = maxlen - len(mchan[nn])
                        mchan[nn] = np.append(mchan[nn], [0]*diff)
                        result.append(mchan[nn])
                mchan = result
        #print(mchan)

        datatocheck = None
        # and isinstance(mchan[0], np.ndarray) and  isinstance(mchan[0][0], np.ndarray):
        if (stats['type'] == 'IMAGE'):
                datatocheck = mchan[0][0][0]
        darray = np.array(mchan)
        # we have array for all train Ids
        #print("Type: ", type(mchan), ",\n", darray)
        #print("Size: ", darray.shape, ",\n", darray)

        groupname = "/" + stats['daqname']  # group name for a channel
        #print(groupname)
        if sub == 0:
            # creating group for a channel
            print(groupname)
            group = fd.create_group(groupname)
            dataset = group.create_dataset(
                "TrainId", dtype="uint64", data=stats['EventID'], compression='gzip', compression_opts=compression, chunks=True, maxshape=(None,))  # creating TrainID dataset
            # creating TimeStamp dataset
            timest = group.create_dataset(
                "TimeStamp", dtype="uint64", data=stats['TimeStamp'], compression='gzip', compression_opts=compression, chunks=True, maxshape=(None, None,))
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
        else:
            dm = None
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
                tp = DAQbasic.bits_to_inttype(
                    int(dm['DIM_EBITPP']), bool(uns))
            if tp == 'unknown':
                # creating data set for values as integers
                data = group.create_dataset(
                    subchname, dtype="int64", data=darray, compression='gzip', compression_opts=compression, chunks=True, maxshape=(None,))
            else:
                # creating data set for values as type from description
                data = group.create_dataset(
                    subchname, dtype=tp, data=darray, compression='gzip', compression_opts=compression, chunks=True, maxshape=(None,))
        else:
            # creating data set for values as float
            if stats['type'] == 'IMAGE':
                #print("Here", type(datatocheck))
                if isinstance(datatocheck, np.uint16):
                    data = group.create_dataset(
                        subchname, dtype="uint16", data=darray, compression='gzip', compression_opts=compression, chunks=True, maxshape=(None,))
                elif isinstance(datatocheck, np.uint8):
                    data = group.create_dataset(
                        subchname, dtype="uint8", data=darray, compression='gzip', compression_opts=compression, chunks=True, maxshape=(None,))
                else:
                    print(stats['daqname'], 'Unsupported data type for image:', type(
                        datatocheck))
            else:
                #print(subchname)
                #print(darray)
                if subchname in group.keys():
                    k = 1
                    lsubchname = subchname + str(k)
                    total_subchan_name_bad += 1
                    while lsubchname in group.keys():
                        k += 1
                        lsubchname = subchname + str(k)
                    subchname = lsubchname
                    if do_print:
                        print("Non standard data set ",
                                    groupname, subchname)
                if darray.ndim == 1:
                    data = group.create_dataset(
                        subchname, dtype="float32", data=darray, compression='gzip', compression_opts=compression, chunks=True, maxshape=(None,))
                else:
                    data = group.create_dataset(
                            subchname, dtype="float32", data=darray, compression='gzip', compression_opts=compression, chunks=True, maxshape=(None, None,))

        if dm != None:
            #print(dm)
            for attr in DAQChanDescr.dimtagstoattr.keys():
                #print(attr)
                if dm[attr] != None:
                    data.attrs[DAQChanDescr.dimtagstoattr[attr]] = dm[attr]
                #   else:
                #       data.attrs[dimtagstoattr[attr]] = "None"
        fd.flush()
        sub += 1


def create_hdf5_file(file, ext=''):
    now = datetime.now()
    timestamp = now.strftime('%Y-%m-%dT%H:%M:%S') + ('-%02d' % (now.microsecond / 10000))

    parts = file.split('/')
    fname = parts[len(parts) -1].split('_main')[0]

    hd5file = dout + fname + '_' + tstart + '_' + tstop + '_' + ext + '.hdf5'
    print('writing into %s . . . \n'%(hd5file), end = '', flush=True)
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
    return fd, hd5file

pickle_files=[]
sz_MB = 0
file_count = 0
def write_hdf5_file_from_pickle_files(file, daqchannels, chandescrlst, ext=''):
    global sz_MB
    total_pfiles = len(pickle_files)

    if not total_pfiles: return None
    file_count = 1
    fd, hd5file = create_hdf5_file(file, ext + '_1')
    basepath = os.path.basename(hd5file)
    for daqchan in daqchannels:

        stats = {}
        for pfile in pickle_files:
            found = False
            stats_list = pickle.load(open(pfile, "rb"))
            for lstats in stats_list:
                if lstats['daqname'] == daqchan:
                    found = True
                    break
            if not found:
                print("%s NOT FOUND in %s"%(daqchan, pfile))
                continue           
            if not len(stats): stats = lstats
            else:
                stats['events'] += lstats['events']
                stats['data'].extend(lstats['data'])
                stats['EventID'].extend(lstats['EventID'])
                stats['TimeStamp'].extend(lstats['TimeStamp'])   
                
        if not len(stats): print('%s not found', daqchan)
        else: 
            #sz =  getsize(stats)
            #print(daqchan, 'events:', stats['events'], 'size in memory:', sz)
            #total_size_in_memory += sz
            #print(stats['EventID'])
            #print(stats['TimeStamp'])
            #print("The size of the dictionary is {} bytes".format(getsize(stats)))
            hd5file = write_data_hdf5_file(fd, stats,  chandescrlst)
            #print(basepath)
            sz =  os.path.getsize(basepath)
            sz_MB = sz/1048576
            if sz_MB > 100:
                file_count += 1
                ext_inc = ext + '_' + str(file_count)
                fd, hd5file = create_hdf5_file(file, ext_inc)
                basepath = os.path.basename(hd5file)
            

    for pfile in pickle_files:
        os.remove(pfile)

    fd.close()
    return hd5file

def write_hdf5_file(file, daqchannels, stats_list, chandescrlst, ext=''):
    global total_subchan_name_bad
    
    fd, hd5file = create_hdf5_file(file, ext)
    h5filelist.append(hd5file)
    for daqchan in daqchannels:
        found = False
        for stats in stats_list:
            if stats['daqname'] == daqchan:
                found = True
                break
        if not found:
            print("%s NOT FOUND"%daqchan)
            continue;    
        hd5file = write_data_hdf5_file(fd, stats,  chandescrlst)
    fd.close()
    return hd5file

def HelpAndExit():
    print("%s: help:\n\n" % (os.path.basename(sys.argv[0])))
    print("The program converts FLASH/XFEL DAQ data raw files  into HDF5 \n")
    print("%s -xml xmlfile [-start stime -stop stime -descr descr_file -dout path -all -xfel -local -c comp  -onefile -evstep nevents -h -print -t] \n" % (os.path.basename(sys.argv[0])))
    print("\t-xml file\t- XML file with DAQ request parameters")
    print("\t-start stime\t- stime is the start time to be used in the request (overwrites XML start time). The format (Year-Month-DayTHour:Min:Sec, eg. 2020-01-01T00:00:00) ")
    print("\t-stop stime\t- stime is the stop time to be used in the request (overwrites XML start time). The format (Year-Month-DayTHour:Min:Sec, eg. 2020-01-01T00:00:00) ")
    print("\t-descr file\t- XML file with DAQ channel descriptions (if not set - default one will be used depending on linac)") 
    print("\t-dout path\t- directory for storing  HDF5 files  (if not set - the current directory will be used") 
    print("\t-all \t\t- consider only those EventIDs where all channels are present (default - all available Event IDs) ")
    print("\t-xfel \t\t- data for XFEL (default: FLASH) ")  
    print("\t-local \t\t- DAQ data extraction local mode will be used (default: DAQ data service)") 
    print("\t-c compr\t- compression level (default: 1) ") 
    print("\t-logic how\t- logic to use for in case of several dest names (default: %s, available: 'AND', 'OR') \n"%logic)
    print("\t-dest name1;name ..\t- beam destination name pattern(s) (eg. TLD;T5D)\n") 
    print("\t-onefile\t- all data to one HDF5 file (default: No) ") 
    print("\t-evstep nevents\t- take every nevents-th event (default 1)")
    print("\t-print \t\t- print data\n")   
    print("\t-t \t\t- convert data according to start/stop time (by default: off - whole files converted)\n")  
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

stats_list = []   # list of dictionaries [ {'daqname':name, 'events':n, 'subch':m, 'type':'DATA_xxx', 'data':[] 'EventID':[] 'TimeStamp':[]} {} ]

if __name__=='__main__':
    global filter_indices
    xmlfile = None
    xmldfile = None
    do_print = False
    xfel = True
    localmode = False
    starttime = None
    stoptime = None
    tstart = None
    tstop = None
    dout = None
    dest = []
    start_time = None
    channel = None
    stop_time = None
    exact_time = False
    all = False
    # Parse command line
    skip = 0
    bunchfilter = None
    compression=1
    onefile=False
    h5filelist = []
    evjump=1
    for i in range(1, len(sys.argv)):
        if not skip:
            if sys.argv[i][:4] == "-xml": (skip,xmlfile)  = NextArg(i)
            elif sys.argv[i][:6] == "-start": (skip,starttime)  = NextArg(i) 
            elif sys.argv[i][:5] == "-stop": (skip,stoptime)  = NextArg(i) 
            elif sys.argv[i][:7] == "-tstart": (skip,tstart)  = NextArg(i) 
            elif sys.argv[i][:6] == "-tstop": (skip,tstop)  = NextArg(i) 
            elif sys.argv[i][:6] == "-filt": (skip,bunchfilter)  = NextArg(i)   
            elif sys.argv[i][:6] == "-descr": (skip,xmldfile)  = NextArg(i)   
            elif sys.argv[i][:5] == "-dout": (skip,dout)  = NextArg(i)      
            elif sys.argv[i][:5] == "-xfel": xfel = True   
            elif sys.argv[i][:5] == "-all": all = True     
            elif sys.argv[i][:5] == "-dest": (skip,dest) = NextArg(i)
            elif sys.argv[i][:6] == "-logic": (skip,logic) = NextArg(i)
            elif sys.argv[i][:6] == "-local": localmode = True   
            elif sys.argv[i][:8] == "-onefile": onefile = True   
            elif sys.argv[i][:2] == "-c": (skip,compression)  = NextArg(i)   
            elif sys.argv[i][:7] == "-evstep":  (skip,evjump) = NextArg(i)   
            elif sys.argv[i][:6] == "-print": do_print = True   
            elif sys.argv[i][:2] == "-t": exact_time = True
            elif sys.argv[i][:2] == "-h": HelpAndExit()
            elif sys.argv[i][:1] == "-":  Fatal("'%s' unknown argument" % sys.argv[i])
            else:                         Fatal("'%s' unexpected" % sys.argv[i])
        else: skip = 0
    timeofstart = datetime.now()
    
    if logic != 'AND' and logic != 'OR':
        print('Invalid logic %s must be AND or OR\n'%logic)
        exit(-1)
    
    if not xmlfile:
        Fatal("Please, check you input arguments")

    evjump = int(evjump)
    #=========================XML request========================================
    if (not os.path.exists(xmlfile)) or (not os.access(xmlfile, os.R_OK)):
        Fatal("XML request file '%s' doesn't exist or not readable" % xmlfile)
    #=========================XML description========================================
    linac = 'XFEL'
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

    if isinstance(compression,str):
        if not compression.isdigit():
            Fatal("Compression level for  HDF5 files '%s' has to be a number" % compression)
        else:
            compression=int(compression)
    
    # setting the default channel for timing information
    if not channel:
        if linac in timing_channels:
            channel = timing_channels[linac]
            print('%s will be used for timing inforamation'%channel)
        else:
            print('Failed to find timing info channel for  %s'%linac)
            sys.exit(-1)    
    
    if dest:
        dest = list(str.split(dest,','))
        print(dest)
        out = []
        for pt in dest:
            p=list(str.split(pt,':'))
            if len(p) == 2:
                out.append({p[0]:p[1]})
            else:
                out.append({p[0]:p[0]})
        dest = out
        print('Pattern to use:',dest)
    else:
        print('No filter by destination applied')

    request = DAQRequest.DAQRequest(xmlfile = xmlfile)
    reqchans = request.getChans()
    if not reqchans:
        reqchans = []
    else:
        res = []
        for sub in reqchans:
            if isinstance(sub, dict):
                res.append(sub['name'])
            else:
                res.append(sub)
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

    #=========================== bunch pattern object ==============================
    
    bp = DAQBunchPattern(linac)

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
    if exact_time:
        start_time = request.getStartTimeSec()
        stop_time = request.getStopTimeSec()
        #print(start_time, stop_time)
    onefile_once = True
    daqfiles_orig = daqfiles
    pickle_index = 0
    filter_indices = []

    for file in daqfiles:
        indexout = []
        indexoutold = []
        
        if not onefile:
            stats_list = []
        xml_request = DAQbasic.prepare_file_request(xml_basic, file)
        #print(xml_request)
        with open(localxmlfile, 'w') as writer:
            writer.write(xml_request)

        daqfiles, daqchannels = DAQbasic.get_channel_file_list(localxmlfile, linac, localmode, True, do_print)
        if reqchans:
            daqchannels = reqchans
        daqchannels.sort()
        #print(daqchannels)
        #print(sys.version)
        print("Working with %d channels\n" %  len(daqchannels))
        #sys.exit(0)
        try:
            err = pydaq.connect(xml=localxmlfile, linac=linac, all=all, local=localmode, cachesize=10000) 
        except pydaq.PyDaqException as err:
            print('Something wrong with connect... exiting')
            print(err)
            os.remove(localxmlfile) 
            sys.exit(-1)
            

        stop = False
        emptycount = 0
        total = 0
        totalevents = 0
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

                totalevents +=1
                if  totalevents%evjump: continue    
                #print(channels)
                nch = 0
                #once = True
                #once2 = True
                if isinstance(channels[0], dict): # slow channels
                    daqnameold = None
                    curentry = None
                    for entry in channels:
                        daqname = entry['miscellaneous']['daqname']
                        timestampsec = int(entry['timestamp']//1)
                        timestampusec = int((entry['timestamp'] % 1)*1000000)
                        if start_time and start_time > timestampsec: continue
                        if stop_time and stop_time <= timestampsec: continue
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
                skip = False
                #chan_list = []
                #for chan in channels:
                #    daqname = chan[0]['miscellaneous']['daqname']
                #    chan_list.append(daqname)
                #if channel not in chan_list:
                #    print(chan_list)
                #    print("%s is not in list."%(channel))
                #    bunchfilter = 'all'
                #    sys.exit(-1)
                
                #indx = chan_list.index(channel)                    
                #if indx != 0:
                #    channels[0], channels[indx] = channels[indx], channels[0]
                    
                for chan in channels:
                    if do_print:
                        print(chan)
                    subchan = len(chan)
                    daqname = chan[0]['miscellaneous']['daqname']
                    timestampsec = int(chan[0]['timestamp']//1)
                    timestampusec = int((chan[0]['timestamp'] % 1)*1000000)
                    if start_time and start_time > timestampsec: 
                        skip = True
                        continue
                    if stop_time and stop_time <= timestampsec: 
                        skip = True
                        continue
                    macropulse =  chan[0]['macropulse']
                    dtype = chan[0]['type']
                    curentry = find_or_create_stat(daqname, macropulse, timestampsec, timestampusec, subchan, dtype, stats_list)
                    chtotal = curentry['events']
                    ##################################### FILTER ADDITION
                    if daqname == channel and bunchfilter != 'all':
                        indexout = []
                        filter_indices = []
                        #indexoutold = []
                        data = chan[0]['data']
                        stamponce = True
                        #print('EventID:', evid[mm], 'Time:', tmst[mm])
                        debug = 0
                        for dt in data:
                            index = int(dt[0])
                            value = dt[1]
                            if value:
                                belong, result =  bp.check_bunch_pattern(value, dest, logic, False)
                                if debug: print(belong, result)
                                if belong:
                                    indexout.append(index)  
                                    filter_indices = [int(index / 2) for index in indexout]
                    ##################################### FILTER ADDITION
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
                                    if (daqname.find("DIAG/BPM/BPM") != -1 or daqname.find("SDIAG/BCM/BCM") != -1 or daqname.find("TOROID/TORA") != -1) and bunchfilter != 'all':
                                        #print('Filter in', daqname)
                                        curentry['data'].append(sub['data'][filter_indices,1])
                                    else:
                                        curentry['data'].append(sub['data'][:,1])                                        
                                else:
                                    #print("This is an IMAGE %dx%d"%(len(data[0]), len(data)))
                                    image = True
                                    curentry['data'].append(sub['data'])                                
                    #sys.exit(0)
                emptycount = 0
                if not skip:
                    total += 1
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
                print(stats['daqname'], ':\t', stats['events'], ' events')
        print('done (total events: %d)'%(total))
        
    # writing to HDF5 file
        if(not onefile):
            write_hdf5_file(file, daqchannels, stats_list, chandescrlst)
            print('done\n')
        else:
            pickle_name = dout+pickle_basic_name+str(pickle_index)+'.p'
            pickle.dump(stats_list, open(pickle_name, "wb")) 
            pickle_files.append(pickle_name)
            stats_list = []
            pickle_index += 1
        os.remove(localxmlfile)

    #stats_list2 = pickle.load(open("mydata.p", "rb"))

    if(onefile):
        write_hdf5_file_from_pickle_files('all'+ daqfiles_orig[0], daqchannels, chandescrlst, ext=bunchfilter)
        print('done total size:', np.round(sz_MB,1), 'MB') 
        if bunchfilter != 'all':
            print('Filtering indices:', filter_indices)
#    else:
#        fd, main_hd5file = create_hdf5_file(daqfiles_orig[0], 'merged')
#        fd.close()
#        print(h5filelist)
#        copy_files_to_one_file(h5filelist, main_hd5file)

    print("All is done. Elapsed time  %s\n"%(str(datetime.now() - timeofstart)))
    if total_subchan_name_bad:
        print("Duplicated sub-channel names: ", total_subchan_name_bad)
