#!/bin/bash
source ~/.profile

## Update the maps .json files
##########################################################################
cd $WEBPAGEDIR/maps/scripts/

echo '--------------------------------------------------' >> updated.log
date >> updated.log

python pull_sne_data.py && echo 'SN update success' >> updated.log
python pull_grbs_data.py && echo 'GRB update success' >> updated.log

git add ../js/sne.json ../js/grbs.json
git commit -m 'SNe & GRB lists updated'
git push

## Update the website to point to the updated files
##########################################################################
cd $WEBPAGEDIR/

git add maps
git commit -m 'Maps updated'
git push