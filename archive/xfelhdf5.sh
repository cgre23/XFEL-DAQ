#!/usr/bin/bash
. /net/xfeluser1/export/doocs/server/daq_server/ENVIRONMENT.new

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH_OLD:/export/doocs/lib:/net/doocsdev16/export/doocs/lib:$LD_LIBRARY_PATH
export PATH=/opt/anaconda/bin:$PATH:/export/doocs/bin
export PYTHONPATH=$PYTHONPATH_OLD:/home/doocsadm/bm/python/DAQ/classes:/export/doocs/lib:/net/doocsdev16/export/doocs/lib:$PYTHONPATH

python daqraw2hdf5.py -xml temp/filtered_stream_channels.xml -xfel -local -descr temp/chann_dscr.xml -onefile -dout ~/Documents/DAQ_files/HDF5

echo "Job finished - exit"
exit
