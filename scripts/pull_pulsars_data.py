'''
A script to properly format the pulsars data, saved as pulsars.txt.
'''

import re, json
import numpy as np
from astro.iAstro import parse_ra, parse_dec, date2jd
from jdcal import jd2gcal
from datetime import datetime
from scipy.interpolate import interp1d, UnivariateSpline

# set to True to get helpful feedback
VERBOSE = True

outf = '/o/ishivvers/public_html/js/plsrs.json'
n_dsteps = 50 #number of distance bins to use

if VERBOSE: print('starting.')
lines = open('pulsars.txt','r').readlines()[7:-1]

if VERBOSE: print('parsing result')
pulsars = []
for line in lines:
    if len(line) < 4: continue
    values = [v for v in line.split(' ') if v]
    try:
        name = values[1]
        coords = [round(float(values[3]),2), round(float(values[4]),2)] #degrees
        eqcoords = [round(float(values[5]),6), round(float(values[6]),6)]
        try:
            period = round(float(values[7]),6) #seconds
        except:
            period= None
        year = values[-1].strip()
        try:
            distance = round(1000*3.262*float(values[25]),2) #lightyears
        except:
            distance = None
        try:
            flux = round(float(values[19]),4) #mJy
        except:
            flux = None

        entry = {'name':name, 'year':year, 'coords':coords, 'eqcoords':eqcoords,
                 'period':period, 'distance':distance, 'flux':flux}
        pulsars.append(entry)
    except:
        if VERBOSE: print('skipping',line)
        if VERBOSE: print(values)
# go through and insert approximations of missing values
# min_flux = np.min( [v['flux'] for v in pulsars if v['flux'] != None] )
# fluxes = [v['flux']-min_flux for v in pulsars if v['flux'] != None]
# max_flux = np.max( fluxes )
# mean_flux = np.mean( fluxes )

fluxes = [v['flux'] for v in pulsars if v['flux'] != None]
mean_flux = round(np.mean(fluxes),4)

mean_dist = np.mean( [v['distance'] for v in pulsars if v['distance'] != None] )
mean_period = np.mean([v['period'] for v in pulsars if v['period'] != None])

for entry in pulsars:
    # put the fluxes onto an absolute scale between 0 and 1
    if entry['flux'] == None:
        entry['flux'] = mean_flux
    if entry['distance'] == None:
        entry['distance'] = round(mean_dist,4)
    if entry['period'] == None:
        entry['period'] = round(mean_period,4)
        
# create a list of distance steps of len n_dsteps with a reasonable number
#  of pulsars in each step
ds = [p['distance'] for p in pulsars]
trim_ds = list(set(ds))
trim_ds.sort()
x = list(range(len(trim_ds)))
X = np.linspace(0,len(trim_ds),n_dsteps)
dsteps = (100*np.round(np.interp(X, x,trim_ds)/100)).tolist()
dsteps[0] = 0.
dsteps[-1] = 150000.
dsteps += [180000.,250000.]

# include a string representing the distance for each
diststrings = []
for i,d in enumerate(dsteps[:-1]):
    d2 = dsteps[i+1]
    if i == 0:
        now = '0'
    else:
        now = str(int(round(d)))
    next = str(int(round(d2)))
    # add a comma into the datestring; need to handle 3-6 digits
    if len(now) > 3:
        now = now[:-3] + ',' + now[-3:]
    if len(next) > 3:
        next = next[:-3] + ',' + next[-3:]
    dstring = now + " - " + next + " lightyears"
    dstring = dstring.replace(' ', '&nbsp;') # use non-breaking space character so the HTML renders correctly
    diststrings.append( dstring )
# and put them into the proper array
binned_ds = np.digitize( ds, dsteps )
pulsers = [None]*len(dsteps)
for i,d in enumerate(ds):
    idist = binned_ds[i] - 1
    if not pulsers[idist]:
        pulsers[idist] = [i]
    else:
        pulsers[idist].append(i)
    pulsars[i]['bin'] = int(idist)

# verify that we got the page properly, and everything is good to go
assert len(pulsars) > 1000
# and write to file
if VERBOSE: print('writing to file')
# now write both the all_sne and the timing variables to file
s = json.dumps(pulsars)
outfile = open(outf, 'w')
outfile.write('all_objs = \n')
outfile.write(s)
s = json.dumps(list(zip(pulsers,diststrings)))
outfile.write('\ntiming_array = \n')
outfile.write(s)
outfile.close()
