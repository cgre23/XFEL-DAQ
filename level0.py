#!/usr/bin/python

import sys
import getopt
import os
import datetime
import string
import time
import pickle
from xml.dom import minidom
import numpy as np
import h5py as h5
import shutil
import subprocess
scriptpath = "../"

timing_channel = 'XFEL.DIAG/TIMINGINFO/TIME1.BUNCH_PATTERN'
name_tag = 'NAME'
channel_list = []
# Add the directory containing your module to the Python path (wants absolute paths)
sys.path.append(os.path.abspath(scriptpath))


def HelpAndExit():
    print("The program converts XFEL DAQ data raw files into HDF5")
    print("Usage: $test.py --start starttime --stop stoptime --xmldfile descr_file --dest destination --dout out_directory")
    print("\t--start stime\t\t- stime is the start time to be used in the request. The format (Year-Month-DayTHour:Min:Sec, eg. 2020-01-01T00:00:00)")
    print("\t--stop stime\t\t- stime is the stop time to be used in the request. The format (Year-Month-DayTHour:Min:Sec, eg. 2020-01-01T00:00:00)")
    print("\t--xmldfile file\t\t- XML file with DAQ channel descriptions")
    print("\t--dest destination\t- Filter bunch either by SA1, SA2 or SA3")
    print("\t--dout path\t\t- directory for storing HDF5 files")
    print("\t-h\t\t- prints this help\n")
    sys.exit(1)


def create_xml(filename, start_time, stop_time, stream_name, channel_list):
    inner_template = string.Template('<Chan name="${name}"/>')
    outer_template = string.Template("""<DAQREQ>
            <TStart time='${starttime}'/>
            <TStop  time='${stoptime}'/>
            <Exp  name='${exp}'/>
            ${document_list}
            <CDir name='/home/grechc/Documents/Datastream/admtemp' />
            </DAQREQ>
             """)
    inner_contents = [inner_template.substitute(
            name=channel) for channel in channel_list]
    out = outer_template.substitute(
            document_list='\n'.join(inner_contents), exp=stream_name, starttime=start_time, stoptime=stop_time)

    write_status = None
    try:
        with open(filename, 'w') as writer:
            writer.write(out)
            write_status = True
    except Exception as err:
        write_status = False
    return out, write_status


def Fatal(msg):
    sys.stderr.write("%s: %s\n\n" % (os.path.basename(sys.argv[0]), msg))
    HelpAndExit()


def deletedirs():
    path = os.getcwd()
    file_path = path + '/tmp/'
    try:
        shutil.rmtree(file_path)
        print("Temp file deleted.")
    except OSError as e:
        print("Error: %s : %s" % (file_path, e.strerror))


def pre_conversion(argv):
    start = None
    stop = None
    xmldfile = None
    dout = None
    bit1 = None
    bit2 = None
    dest = None
    try:
        opts, args = getopt.getopt(
            argv, "hs:t:c:d:o", ["start=", "stop=", "xmldfile=", "dest=", "dout="])
    except getopt.GetoptError:
        HelpAndExit()
    for opt, arg in opts:
        if opt == '-h':
            HelpAndExit()
        elif opt in ("-s", "--start"):
            start = arg
        elif opt in ("-t", "--stop"):
            stop = arg
        elif opt in ("-c", "--xmldfile"):
            xmldfile = arg
        elif opt in ("-d", "--dest"):
            dest = arg
        elif opt in ("-o", "--dout"):
            dout = arg
    print('Start time is: ', start)
    print('Stop time is: ', stop)
    print('Desc is: ', xmldfile)
    print('Dest is: ', dest)
    print('Output folder is: ', dout)

    if not dout:
        dout = './'
    if (not os.path.exists(dout)) or (not os.access(dout, os.W_OK)):
        Fatal("Directory for  HDF5 files '%s' doesn't exist or not writable" % dout)

    if not dout.endswith('/'):
        dout += '/'

    if not start or not stop or not xmldfile:
        Fatal("Please, check you input arguments and make sure to insert at least a start time, stop time and description file")

    if start:
        try:
            starttime = int(datetime.datetime.strptime(
                start, '%Y-%m-%dT%H:%M:%S').timestamp())
        except:
            Fatal(
                "Please, check start time format '%s'. It must be 'Year-Month-DayTHour:Min:Sec' " % start)

    if stop:
        try:
            stoptime = int(datetime.datetime.strptime(
                stop, '%Y-%m-%dT%H:%M:%S').timestamp())
        except:
            Fatal(
                "Please, check stop time format '%s'. It must be 'Year-Month-DayTHour:Min:Sec' " % stop)

    if stoptime <= starttime:
        Fatal("Please, check that stop time is later than the start time.")

    if (not os.path.exists(xmldfile)) or (not os.access(xmldfile, os.R_OK)):
        Fatal("XML description file '%s' doesn't exist or not readable" % xmldfile)

    if dest:
        if dest == 'SA1':
            bit1 = 'Destination:T4D\ \(SASE1/3\ dump\)'
            bit2 = 'Special\ Flags:SASE3\ soft\ kick\ \(T4\)'
            bunchfilter = 'SA1'
        elif dest == 'SA2':
            bit1 = 'Destination:T5D\ \(SASE2\ dump\)'
            bit2 = 'Special\ Flags:Beam\ distribution\ kicker\ \(T1\)'
            bunchfilter = 'SA2'
        elif dest == 'SA3':
            bit1 = 'Destination:T4D\ \(SASE1/3\ dump\)'
            bit2 = 'Special\ Flags:Soft\ kick\ \(e.g.SA3\)'
            bunchfilter = 'SA3'
        else:
            print('Destination not recognized')
            bunchfilter = 'all'
        print('Pattern to use:', bit1, bit2)
    else:
        print('No filter by destination applied')
        bunchfilter = 'all'

    xmldoc = minidom.parse(xmldfile)
    itemlist = xmldoc.getElementsByTagName(name_tag)

    for s in itemlist:
        channel_list.append(s.firstChild.nodeValue)

    if timing_channel not in channel_list:
        print("%s is not in list." % (timing_channel))
        #    bunchfilter = 'all'
        sys.exit(-1)

    indx = channel_list.index(timing_channel)
    if indx != 0:
        channel_list[0], channel_list[indx] = channel_list[indx], channel_list[0]

    streamname = os.path.basename(xmldfile).split('_main')[0]
    print('Detected stream: ', streamname)
    # saving the updated XML request file
    dest_dir = 'tmp'
    try:
        os.makedirs(dest_dir)
    except OSError:
        pass  # already exists

    tmpxmlfile = 'xfelrequest.xml'
    xmlpath = os.path.join(dest_dir, tmpxmlfile)
    xml, res = create_xml(xmlpath, start, stop, streamname, channel_list)

    if not res:
        print('Failed to create XML file %s ... exiting' % tmpxmlfile)
        sys.exit(-1)
    else:
        print('XML file created')

    return start, stop, bit1, bit2, xmldfile, xmlpath, bunchfilter


if __name__ == "__main__":
    start, stop, filter_bit1, filter_bit2, xmldfile, xmlfile, bunchfilter = pre_conversion(
        sys.argv[1:])

    startstring = start.replace('-', '')
    startstring = startstring.replace(':', '')
    stopstring = stop.replace('-', '')
    stopstring = stopstring.replace(':', '')

    command = "export PYTHONPATH=/beegfs/desy/group/mpa/fla/software/daq/libs/CentOS-7-x86_64; export LD_LIBRARY_PATH=/beegfs/desy/group/mpa/fla/software/daq/libs/CentOS-7-x86_64:/beegfs/desy/group/mpa/fla/software/daq/libs/CentOS-7-x86_64/extlib; python3 daqraw2hdf5_filter.py -xml %s -xfel -onefile -local -descr %s -logic AND -dest %s,\%s -tstart %s -tstop %s -filt %s" % (
        '~/Documents/Datastream/SASE2_BPM_extraction/linac.xml', xmldfile, filter_bit1, filter_bit2, startstring, stopstring, bunchfilter)
    print(command)
    subprocess.run(command, shell=True)
