import sys
import os

import time
import pickle

import numpy as np
import h5py as h5


#from datetime import datetime
#from datetime import timedelta
#import collections

#import classes.DAQbasic as DAQbasic
#import classes.DAQRequest as DAQRequest
#import classes.DAQChanDescr as DAQChanDescr
import classes.DAQChanDescrList as DAQChanDescrList


scriptpath = "../"

# Add the directory containing your module to the Python path (wants absolute paths)
sys.path.append(os.path.abspath(scriptpath))


def Fatal(msg):
    sys.stderr.write("%s: %s\n\n" % (os.path.basename(sys.argv[0]), msg))
    sys.exit(1)


if __name__ == '__main__':
    starttime = sys.argv[1]
    stoptime = sys.argv[2]
    xmldfile = sys.argv[3]

if (not os.path.exists(xmldfile)) or (not os.access(xmldfile, os.R_OK)):
    Fatal("XML description file '%s' doesn't exist or not readable" % xmldfile)

chandescrlst = DAQChanDescrList.ChanDescrList(
    xmlfile=xmldfile, chans=[]).GetDescriptionList()

print(chandescrlst)
