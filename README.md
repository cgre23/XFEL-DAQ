# XFEL-DAQ-Datastream-Parser

Author: Christian Grech (christian.grech@desy.de)

Software to convert DAQ files from XFEL DAQ Datastreams and Karabo to a table format (parquet).

* level0.py - Gets data from XFEL DAQ datastreams (linac, xfel_sase1 etc...) and filters BPMs, Toroids and BCM by bunch destination (SA1, SA2 or SA3) Data is stored as HDF5 files.

Example:
python3 level0.py --start 2021-11-17T15:02:00 --stop 2021-11-17T15:02:05 --xmldfile xml/xfel_sase1_main_run1727_chan_dscr.xml --dest SA1

* level0_karabo.py - Gets data from Karabo. Data is stored as HDF5 files.

Example:
python3 level0_karabo.py --proposal 2919 --run 1

* daq_parser_v2.py - GUI interface to export selected channels in a specific timestamp range to a parquet format.

--start 2022-10-16T18:10:00 --stop 2022-10-16T18:11:00 --xmldfile /daq/xfel/admtemp/2022/linac/main/run1982/linac_main_run1982_chan_dscr.xml --xmlfile xml/sase2.xml