#!/usr/bin/python

import sys
import getopt
import os
import datetime
import string
import time
import numpy as np
import h5py as h5
import shutil
from extra_data import open_run
scriptpath = "../"

timing_channel = 'XFEL.DIAG/TIMINGINFO/TIME1.BUNCH_PATTERN'
name_tag = 'NAME'
channel_list = []
# Add the directory containing your module to the Python path (wants absolute paths)
sys.path.append(os.path.abspath(scriptpath))


def HelpAndExit():
    print("The program converts Extra Data DAQ data run files into HDF5")
    print("Usage: $level0_extra_data.py --proposal proposal_no --run run_no --dout out_directory")
    print("\t--proposal proposal_no\t\t- proposal_no is the experiment proposal number, ex: 2919")
    print("\t--run run_no\t\t- run_no is the run number to be exported. The format is 1 for example. You can include more than one run.")
    print("\t--dout path\t\t- directory for storing HDF5 files")
    print("\t-h\t\t- prints this help\n")
    sys.exit(1)


def Fatal(msg):
    sys.stderr.write("%s: %s\n\n" % (os.path.basename(sys.argv[0]), msg))
    HelpAndExit()


def pre_conversion(argv):
    proposal = None
    runs = []
    dout = None
    dest = None
    try:
        opts, args = getopt.getopt(
            argv, "hs:t:c:d:o", ["proposal=", "run=", "dout="])
    except getopt.GetoptError:
        HelpAndExit()
    for opt, arg in opts:
        if opt == '-h':
            HelpAndExit()
        elif opt in ("-s", "--proposal"):
            proposal = arg
        elif opt in ("-t", "--run"):
            runs.append(arg)
        elif opt in ("-o", "--dout"):
            dout = arg
    print('Proposal num is: ', proposal)
    print('Runs are: ', runs)
    print('Output folder is: ', dout)

    if not dout:
        dout = './'
    if (not os.path.exists(dout)) or (not os.access(dout, os.W_OK)):
        Fatal("Directory for  HDF5 files '%s' doesn't exist or not writable" % dout)

    if not dout.endswith('/'):
        dout += '/'

    if not proposal or not runs:
        Fatal("Please, check you input arguments and make sure to insert at least a proposal number and a runs list")

    if proposal:
        try:
            proposal_int = int(proposal)
        except:
            Fatal(
                "Please, check proposal format '%s'. It must be an integer. " % proposal)

    if runs:
        try:
            runs_list = list(runs)
        except:
            Fatal("Please, check run format '%s'. It must be an integer e.g 1 . " % runs)

    return proposal_int, runs_list


if __name__ == "__main__":
    proposal_no, runs_list = pre_conversion(sys.argv[1:])

    for num in runs_list:
        run = open_run(proposal=proposal_no, run=num)
        delta = np.timedelta64(1, 'h')
        start_timestamp = run.train_timestamps()[0] + delta
        stop_timestamp = run.train_timestamps()[-1] + delta

        start_string = np.datetime_as_string(start_timestamp, unit='s')
        start_string = start_string.replace("-", "").replace(":", "")

        stop_string = np.datetime_as_string(stop_timestamp, unit='s')
        stop_string = stop_string.replace("-", "").replace(":", "")

        filename = os.getcwd() + '/extra/extra_data_' + start_string + \
            '_' + stop_string + '_all.h5'
        run.write(filename)
