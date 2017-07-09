#!/bin/bash
source ~/.profile

##########################################################################
cd $WEBPAGEDIR/maps/scripts/

echo '--------------------------------------------------' >> updated.log
date >> updated.log

python pull_sne_data.py && echo 'SN update success' >> updated.log
python pull_grbs_data.py && echo 'GRB update success' >> updated.log

git add -u
git commit -m 'SNe & GRB lists updated'
git push

##########################################################################
cd $WEBPAGEDIR/

# git add -u
# git commit -m 'Maps updated'
# git push