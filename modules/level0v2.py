#!/usr/bin/python

import sys
import getopt
import os
import datetime
import string
import time
import pickle
import numpy as np
#import h5py as h5
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
    print("\t--dest destination\t- Filter bunch either by SA1, SA2 or SA3")
    print("\t--dout path\t\t- directory for storing HDF5 files")
    print("\t-h\t\t- prints this help\n")
    sys.exit(1)


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
    dout = None
    bit1 = None
    bit2 = None
    dest = None
    try:
        opts, args = getopt.getopt(
            argv, "hs:t:c:d:o", ["start=", "stop=", "dest=", "dout="])
    except getopt.GetoptError:
        HelpAndExit()
    for opt, arg in opts:
        if opt == '-h':
            HelpAndExit()
        elif opt in ("-s", "--start"):
            start = arg
        elif opt in ("-t", "--stop"):
            stop = arg
        elif opt in ("-d", "--dest"):
            dest = arg
        elif opt in ("-o", "--dout"):
            dout = arg
    print('Start time is: ', start)
    print('Stop time is: ', stop)
    print('Dest is: ', dest)
    print('Output folder is: ', dout)

    if not dout:
        dout = './'
    if (not os.path.exists(dout)) or (not os.access(dout, os.W_OK)):
        Fatal("Directory for  HDF5 files '%s' doesn't exist or not writable" % dout)

    if not dout.endswith('/'):
        dout += '/'

    if not start or not stop or not dest:
        Fatal("Please, check you input arguments and make sure to insert at least a start time, stop time and a destination.")

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

    if dest:
        if dest == 'SA1':
            bit1 = 'Destination:T4D\ \(SASE1/3\ dump\)'
            bit2 = 'Special\ Flags:SASE3\ soft\ kick\ \(T4\)'
            bunchfilter = 'SA1'
            xmlfile = 'xml/xfel_sase1.xml'
        elif dest == 'SA2':
            bit1 = 'Destination:T5D\ \(SASE2\ dump\)'
            bit2 = 'Special\ Flags:Beam\ distribution\ kicker\ \(T1\)'
            bunchfilter = 'SA2'
            xmlfile = 'xml/xfel_sase2.xml'
        elif dest == 'SA3':
            bit1 = 'Destination:T4D\ \(SASE1/3\ dump\)'
            bit2 = 'Special\ Flags:Soft\ kick\ \(e.g.SA3\)'
            bunchfilter = 'SA3'
            xmlfile = 'xml/xfel_sase3.xml'
        else:
            print('Destination not recognized')
            bunchfilter = 'all'
            xmlfile = 'xml/xfel_sase1.xml'
        print('Pattern to use:', bit1, bit2)
    else:
        print('No filter by destination applied')
        bunchfilter = 'all'
        xmlfile = 'xml/xfel_sase1.xml'

    #xmlpath = os.path.join(dest_dir, xmlfile)

    return start, stop, bit1, bit2, xmlfile, bunchfilter


if __name__ == "__main__":
    start, stop, filter_bit1, filter_bit2, xmlfile, bunchfilter = pre_conversion(
        sys.argv[1:])

    command = ". /net/xfeluser1/export/doocs/server/daq_server/ENVIRONMENT.new; export LD_LIBRARY_PATH=$LD_LIBRARY_PATH_OLD:/export/doocs/lib:/net/doocsdev16/export/doocs/lib:$LD_LIBRARY_PATH; export PATH=/opt/anaconda/bin:$PATH:/export/doocs/bin; export PYTHONPATH=$PYTHONPATH_OLD:/home/doocsadm/bm/python/DAQ/classes:/export/doocs/lib:/net/doocsdev16/export/doocs/lib:$PYTHONPATH; python3 modules/daqraw2hdf5_filter.py -xml %s -xfel -onefile -local -logic AND -dest %s,\%s -start %s -stop %s -filt %s" % (xmlfile, filter_bit1, filter_bit2, start, stop, bunchfilter)
    print(command)
    subprocess.run(command, shell=True)
