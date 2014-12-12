'''
A script to scrape the up-to-date SN info from
http://www.cbat.eps.harvard.edu/lists/Supernovae.html
and format it properly.
'''

import urllib2, re, json, ephem
import numpy as np
from iAstro import parse_ra, parse_dec, date2jd
from jdcal import jd2gcal
import os, urllib2
from datetime import datetime
from scipy.interpolate import UnivariateSpline
import mechanize

def remove_tags( row ):
    '''returns row with HTML tags removed, for easy parsing'''
    # strip tags
    intag = False
    outstr = []
    for char in row:
        if char == '<':
            intag = True
        elif char == '>':
            intag = False
        else:
            if not intag:
                outstr.append(char)
    return ''.join(outstr)
    

outf = '/o/ishivvers/public_html/js/grbs.json'
n_tsteps = 600 # if 100ms per step, this works out to 1 minute of playtime
# note: this is just a value to aim for, doesn't get it exactly

months = {1:'Jan.',2:'Feb.',3:'Mar.',4:'Apr.',5:'May',6:'June',
          7:'July',8:'Aug.',9:'Sep.',10:'Oct.',11:'Nov.',12:'Dec.'}
'''
Parse the historical grbcat
'''

print 'processing grbcat'
grbs = []
jds = []
t90_list = []
rows = [r.strip() for r in open('grbcat.txt','r').readlines() if r[0]=='|']
for row in rows[1:]:
    try:
        items = row.split('|')
        name = items[1].strip().strip('GRB ')
        obsstring = items[2].strip()
        decimal = re.findall('\.\d',obsstring)
        if decimal:
            obsstring = obsstring[:-2]
        try:
            time = datetime.strptime(obsstring, '%Y-%m-%d %H:%M:%S')
        except:
            time = datetime.strptime(obsstring, '%Y-%m-%d')
        timestr = '{} {}, {} {}:{}:{}'.format( months[time.month], time.day, time.year, time.hour, time.minute, time.second)
        if not (items[4].strip() and items[5].strip()):
            raise IOError()
        ra = parse_ra(items[4])
        dec = parse_dec(items[5])
        coords = ephem.Equatorial(np.deg2rad(ra), np.deg2rad(dec))
        galcoords = ephem.Galactic(coords)
        observatory = items[3].strip()
        if not observatory:
            observatory = None
        # don't include swift sources, since they get added below
        if observatory == 'SWIFT':
            continue
        # go through and find a time, preferring: t90 > t50 > t_other
        t90 = None
        for i in [7,6,8]:
            try:
                t90 = float(items[i].strip())
                if t90 == 0:
                    t90 = None
                else:
                    break
            except:
                continue
        entry = {'name':name, 'eqcoords':[round(ra,6), round(dec,6)], 'observatory':observatory,
                 'date':timestr, 'coords':[round(np.rad2deg(galcoords.lon),2), round(np.rad2deg(galcoords.lat),2)]}
        if t90 > 0:
            entry['t90'] = round(t90,4)
            t90_list.append(t90)
        grbs.append(entry)
        jds.append(date2jd(time))
    except:
        print 'skipping',row
# now insert any missing info and remove dupes
grbcat_grbs = []
grbcat_names = []
grbcat_jds = []
mean_t90 = round(np.mean(t90_list),4)
for iii,entry in enumerate(grbs):
    if t90 not in entry.keys():
        entry['t90'] = mean_t90
    if entry['name'] in grbcat_names:
        # ignore the catalog observatories, otherwise simply keep the most recent listing of the grb
        if entry['observatory'] == 'CATALOG':
            continue
        else:
            i_dupe = grbcat_names.index(entry['name'])
            grbcat_grbs.pop(i_dupe)
            grbcat_names.pop(i_dupe)
            grbcat_jds.pop(i_dupe)
    grbcat_names.append(entry['name'])
    grbcat_grbs.append(entry)
    grbcat_jds.append(jds[iii])

print 'processing swift table'
page = urllib2.urlopen('http://swift.gsfc.nasa.gov/docs/swift/archive/grb_table.html/'+\
                       'grb_table.php?obs=All+Observatories&year=All+Years&restrict=none&'+\
                       'grb_time=1&redshift=1&host=1&bat_ra=1&bat_dec=1&bat_t90=1&bat_fluence=1&'+\
                       'view.x=26&view.y=10&view=submit').read()
table = page.split('<table')[1].split('</table>')[0]
entries = table.split('</tr>')
swift_grbs = []
swift_jds = []
swift_fluences = []
for entry in entries[1:]:
    values = []
    row = entry.split('</td>')
    # make sure this is not an empty row
    if len(row) < 2:
        continue
    # periodically, there is a header row
    if 'GRB' in row[0]:
        continue
    # some sources are not localized
    if 'n/a' in row[2] or 'n/a' in row[3]:
        continue
    for i in range(len(row)):
        if i in [2,3]:
            # do some gymnastics to get the proper RA and Dec out
            try:
                values.append(remove_tags(row[i].split('<br />')[1]).strip())
            except:
                try:
                    values.append(remove_tags(row[i].split('<br>')[1]).strip())
                except:
                    values.append(remove_tags(row[i]).strip())
        else:
            values.append(remove_tags(row[i]).strip())
    name = values[0]
    obsstring = values[1]
    decimal = re.findall('\.\d+',obsstring)
    if decimal:
        obsstring = obsstring.split(decimal[0])[0]
    # use the name to get the date
    obsstring = re.findall('\d+', name)[0] + ' ' + obsstring
    try:
        time = datetime.strptime(obsstring, '%y%m%d %H:%M:%S')
    except:
        time = datetime.strptime(re.findall('\d+', name)[0], '%y%m%d')
    timestr = '{} {}, {} {}:{}:{}'.format( months[time.month], time.day, time.year, time.hour, time.minute, time.second)
    ra = parse_ra(values[2])
    dec = parse_dec(values[3])
    try:
        t90 = float(values[4])
    except:
        t90 = mean_t90
    try:
        fluence = float(values[5])
        swift_fluences.append(fluence)
    except:
        fluence = None
    observatory = 'SWIFT'
    coords = ephem.Equatorial(np.deg2rad(ra), np.deg2rad(dec))
    galcoords = ephem.Galactic(coords)
    entry = {'name':name, 'eqcoords':[round(ra,6), round(dec,6)], 'observatory':observatory, 't90':round(t90,4),
             'date':timestr, 'coords':[round(np.rad2deg(galcoords.lon),2), round(np.rad2deg(galcoords.lat),2)]}
    if fluence > 0:
        entry['fluence'] = fluence
    swift_grbs.append(entry)
    swift_jds.append(date2jd(time))
# put the fluences onto an absolute scale between 0 and 1
min_fluence = np.min(swift_fluences)
swift_fluences = np.array(swift_fluences) - min_fluence
max_fluence = np.max(swift_fluences)
mean_fluence = np.mean(swift_fluences)
for grb in swift_grbs:
    if 'fluence' in grb.keys():
        grb['fluence'] = round(grb['fluence']/max_fluence,4)
    else:
        grb['fluence'] = round(mean_fluence/max_fluence,4)
# use the mean SWIFT fluences to insert values for GRBCAT
for grb in grbcat_grbs:
    grb['fluence'] = round(mean_fluence/max_fluence,4)

print 'processing fermi table'
rows_wanted = ['name','ra','dec','trigger_time','t90','fluence']
br = mechanize.Browser()
br.set_handle_robots(False)
ws = 'http://heasarc.gsfc.nasa.gov/db-perl/W3Browse/w3table.pl?tablehead=name%3Dfermigbrst&Action=More+Options'
br.open(ws)
br.select_form(nr=0)
# select only the rows we want
checkboxes = br.find_control(type="checkbox", name="varon").items
for box in checkboxes:
    if box.name in rows_wanted:
        box.selected = True
    else:
        box.selected = False
# make sure to return all responses
limits = br.find_control(name="ResultMax").items
for lim in limits:
    if lim.name == '0':
        lim.selected = True
    else:
        lim.selected = False
# return a simple text table
display_modes = br.find_control(name="displaymode").items
for mode in display_modes:
    if mode.name == 'TextDisplay':
        mode.selected = True
    else:
        mode.selected = False
# finally, submit the form
response = br.submit()
src = response.read()
rows = src.split('Select All')[1].split('Data Products Retrieval')[0].split('\n')
# now go through and actually process them
grbs = []
jds = []
fermi_fluences = []
for row in rows:
    if row[:20] != '<a target="moreinfo"': continue
    values = remove_tags(row).split('|')
    name = values[1].strip().strip('GRB')[:6] #use only the date (not the time) for GRB name
    ra = parse_ra(values[2])
    dec = parse_dec(values[3])
    obsstring = values[4].strip()
    decimal = re.findall('\.\d+',obsstring)
    if decimal:
        obsstring = obsstring.split(decimal[0])[0]
    time = datetime.strptime(obsstring, '%Y-%m-%d %H:%M:%S')
    timestr = '{} {}, {} {}:{}:{}'.format( months[time.month], time.day, time.year, time.hour, time.minute, time.second)
    try:
        t90 = float(values[5])
    except:
        t90 = mean_t90
    try:
        fluence = float(values[6])
        fermi_fluences.append(fluence)
    except:
        fluence = None
    observatory = 'FERMI'
    coords = ephem.Equatorial(np.deg2rad(ra), np.deg2rad(dec))
    galcoords = ephem.Galactic(coords)
    entry = {'name':name, 'eqcoords':[round(ra,6), round(dec,6)], 'observatory':observatory, 't90':round(t90,4),
             'date':timestr, 'coords':[round(np.rad2deg(galcoords.lon),2), round(np.rad2deg(galcoords.lat),2)]}
    if fluence > 0:
        entry['fluence'] = fluence
    grbs.append(entry)
    jds.append(date2jd(time))
# go through and put in fluence values on an absolute scale between 1 and 0
min_fluence = np.min(fermi_fluences)
fermi_fluences = np.array(fermi_fluences) - min_fluence
max_fluence = np.max(fermi_fluences)
mean_fluence = np.mean(fermi_fluences)
for grb in grbs:
    if 'fluence' in grb.keys():
        grb['fluence'] = round(grb['fluence']/max_fluence,4)
    else:
        grb['fluence'] = round(mean_fluence/max_fluence,4)
    
# go through and drop any doubles between Fermi and Swift (prefer SWIFT)
fermi_grbs = []
fermi_jds = []
swift_ns = [g['name'][:6] for g in swift_grbs]
for i,grb in enumerate(grbs):
    n = grb['name'][:6]
    if n in swift_ns:
        continue
    else:
        fermi_grbs.append(grb)
        fermi_jds.append(jds[i])
# at this point, there appear to be no double names, so I will not worry about
#  adding in an A,B,C, etc.

grbs = grbcat_grbs + swift_grbs + fermi_grbs
jds = grbcat_jds + swift_jds + fermi_jds


# create a list of timesteps of len n_tsteps with a reasonable number of GRBs in each
trim_jds = list(set(jds))
trim_jds.sort()
timesteps = np.round(np.array(trim_jds)[:: len(trim_jds)/n_tsteps ],1)
# make sure the last day is after the last actual explosion
timesteps[-1] = round(trim_jds[-1] + 1, 1)
# make sure that first day is before the first explosion
timesteps[0] = timesteps[0] - 1

# include a string representing the year and month of each
datestrings = []
for i,t in enumerate(timesteps[:-1]):
    now = jd2gcal(0,t)
    next = jd2gcal(0,timesteps[i+1])
    ds = str(months[now[1]]).ljust(5) + str(now[2]).rjust(2) + str(now[0]).rjust(5) + " - " +\
         str(months[next[1]]).ljust(5) + str(next[2]).rjust(2) + str(next[0]).rjust(5)
    ds = ds.replace(' ', '&nbsp;') # use non-breaking space character so the HTML renders correctly
    datestrings.append( ds )
# create a timing array that includes all GRBs to explode in a certain range
binned_jds = np.digitize( jds, timesteps )
explosions = [None]*len(datestrings)
for i,jd in enumerate(jds):
    iexplode = binned_jds[i] - 1
    if not explosions[iexplode]:
        explosions[iexplode] = [i]
    else:
        explosions[iexplode].append(i)
    grbs[i]['bin'] = int(iexplode)

# also include a flag, to show which values were measured versus averaged
#  (0=all measured, 1=only timing, 2=only flux, 3=both averaged)
for grb in grbs:
    if (grb['fluence'] == round(mean_fluence/max_fluence,4)) and (grb['t90'] == round(mean_t90,4)):
        grb['flag'] = 3
    elif (grb['fluence'] == round(mean_fluence/max_fluence,4)):
        grb['flag'] = 1
    elif (grb['t90'] == round(mean_t90,4)):
        grb['flag'] = 2
    else:
        grb['flag'] = 0
        
# and write to file
print 'writing to file'
# now write both the all_sne and the timing variables to file
s = json.dumps(grbs)
outfile = open(outf, 'w')
outfile.write('all_objs = \n')
outfile.write(s)
s = json.dumps(zip(explosions,datestrings))
outfile.write('\ntiming_array = \n')
outfile.write(s)
outfile.close()
print 'done!'


