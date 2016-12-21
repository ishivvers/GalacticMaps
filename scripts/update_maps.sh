#!/usr/local/bin/bash
### a script to update the data behind the maps pages ###

source /o/ishivvers/.bashrc
cd /o/ishivvers/MapsWebsiteSupport

echo '--------------------------------------------------' >> updated.log
date >> updated.log

/big_scr5/ishivvers/anaconda/bin/python pull_sne_data.py && echo 'SN update success' >> updated.log
/big_scr5/ishivvers/anaconda/bin/python pull_grbs_data.py && echo 'GRB update success' >> updated.log

