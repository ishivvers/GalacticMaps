'''
A script to scrape the up-to-date SN info from
http://www.cbat.eps.harvard.edu/lists/Supernovae.html
and format it properly.
'''

import urllib.request, urllib.parse, urllib.error, re, json, ephem
import numpy as np
from iAstro import parse_ra, parse_dec, date2jd
from jdcal import jd2gcal
from datetime import datetime
from scipy.interpolate import UnivariateSpline
from bs4 import BeautifulSoup

# set to True to get helpful feedback
VERBOSE = False

outf = 'js/sne.json'

n_tsteps = 600 # if 100ms per step, this works out to 1 minute of playtime

#months = {1:'January',2:'February',3:'March',4:'April',5:'May',6:'June',
#          7:'July',8:'August',9:'September',10:'October',11:'November',12:'December'}
months = {1:'Jan.',2:'Feb.',3:'Mar.',4:'Apr.',5:'May',6:'June',
          7:'July',8:'Aug.',9:'Sep.',10:'Oct.',11:'Nov.',12:'Dec.'}

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

#####################################
# First pull the Rochester page info
#####################################

def download_historical_rochester_info():
    """
    Parse the huge rochester SN page and produce a dictionary akin
     to that produced by download_current_rochester_info.
    """
    uri = 'http://www.rochesterastronomy.org/snimages/sndateall.html'
    page = urllib.request.urlopen( uri ).read()
    soup = BeautifulSoup(page, features="html5lib")
    table = soup.findAll("table")[1]

    C_ROCHESTER_DICT = {}
    rows = table.findAll("tr")
    for row in rows[1:]:
        vals = row.findAll("td")
        if len(vals) == 1:
            continue
        try:
            ra = parse_ra( vals[0].getText() )
            dec = parse_dec( vals[1].getText() )
            date = vals[2].getText()
            host = vals[6].getText()
            sn_type = vals[7].getText()
            mag = float(vals[9].getText())
            name = vals[10].getText()
            altName = vals[11].getText()
            discoverer = '' # not present in this table
            ref_link = '' # not present in this table
            
            C_ROCHESTER_DICT[name] = [host, ra, dec, sn_type, ref_link, date, discoverer, mag]
        except:
            # just continue on errors
            # print row
            pass
    return C_ROCHESTER_DICT

def download_current_rochester_info():
    """
    Parse the current rochester SN page and produce a dictionary including
     all the rows we can understand.
    This page has quite a few entries with slightly odd entries, and this script
     is my best effort to parse most of them, but there are definitely some that
     break this and are not included.  Oh well.
    """
    uri = 'http://www.rochesterastronomy.org/snimages/snactive.html'
    page = urllib.request.urlopen( uri ).read()
    soup = BeautifulSoup(page, features="html5lib")
    tables = soup.findAll("table")[1:]

    C_ROCHESTER_DICT = {}
    for t in tables:
        rows = t.findAll("tr")
        for row in rows[1:]:
            vals = row.findAll("td")
            if len(vals) == 1:
                continue
            try:
                name = vals[0].getText()
                host = vals[1].getText()
                ra = parse_ra( vals[2].getText() )
                dec = parse_dec( vals[3].getText() )
                mag = float(vals[9].getText())
                sn_type = vals[7].getText()
                ref_link = None # not present in this table
                date = vals[11].getText()
                discoverer = vals[12].getText()
                C_ROCHESTER_DICT[name] = [host, ra, dec, sn_type, ref_link, date, discoverer, mag]
            except:
                pass
    return C_ROCHESTER_DICT

##################################

if VERBOSE: print('opening historical Rochester page and parsing result.')
rocd = download_historical_rochester_info()
SNe = []
jds = []

for sn in list(rocd.keys()):
    try:
        # get coords
        snRA = rocd[sn][1]
        snDec = rocd[sn][2]
        # get Gregorian and Julian discovery date
        date = datetime.strptime( rocd[sn][5].split('.')[0], '%Y/%m/%d')
        datestr = '{} {}, {}'.format( months[date.month], date.day, date.year)
        # get the type, host, and max brightness
        sntype = rocd[sn][3]
        if sntype == 'unk':
            sntype = None
            raise Exception('not confirmed.')
        if sntype in ['CV', 'CV?', 'LBV', 'LBV?']:
            raise Exception('not a sn')
        gal = rocd[sn][0]
        mag = rocd[sn][7]
        name = sn
        # some are bad:
        if name in ['PS1-14vd']:
            raise Exception('bullshit!')
        # add 'SN' if needed
        if re.search('^\d{4}.*', name) and 'Possible' not in name:
            name = 'SN '+name
        authors = rocd[sn][6] # usually blank from this page

        # now assemble this for the website, but only if it's after year 2000
        #  (use other page as early authority, for simplicity).
        if date.year < 2000:
            continue
        # put an extra couple tests here, since mis-parsed magnitudes can be noticible
        if mag > 30:
            raise Exception('Misparsed: Mag too faint')
        if mag < 3.0:
            # 1987A was mag 4.5
            raise Exception('Misparsed: Mag too bright')
        dictentry = {'name':name, 'galaxy':gal, 'date':datestr,
                     'magnitude':mag, 'type':sntype, 'authors':authors}
        coords = ephem.Equatorial(np.deg2rad(snRA), np.deg2rad(snDec))
        dictentry['eqcoords'] = [round(snRA,6), round(snDec,6)]
        galcoords = ephem.Galactic(coords)
        dictentry['coords'] = [round(np.rad2deg(galcoords.lon),2), round(np.rad2deg(galcoords.lat),2)]
        SNe.append(dictentry)
        jds.append(date2jd(date))
    except Exception as e:
        if VERBOSE: print(('skipping',sn,rocd[sn],":",e))
print(f'adding {len(SNe)} from historical rochester page')

if VERBOSE: print('opening current Rochester page and parsing result.')
rocd = download_current_rochester_info()
SNe2 = []
jds2 = []

for sn in list(rocd.keys()):
    try:
        # get coords
        snRA = rocd[sn][1]
        snDec = rocd[sn][2]
        # get Gregorian and Julian discovery date
        date = datetime.strptime( rocd[sn][5].split('.')[0], '%Y/%m/%d')
        datestr = '{} {}, {}'.format( months[date.month], date.day, date.year)
        # get the type, host, and max brightness
        sntype = rocd[sn][3]
        if sntype == 'unk':
            sntype = None
            raise Exception('not confirmed.')
        if sntype in ['CV', 'CV?', 'LBV', 'LBV?']:
            raise Exception('not a sn')
        gal = rocd[sn][0]
        mag = rocd[sn][7]
        name = sn
        # some are bad:
        if name in ['PS1-14vd']:
            raise Exception('bullshit!')
        # add 'SN' if needed
        if re.search('^\d{4}.*', name) and 'Possible' not in name:
            name = 'SN '+name
        # the rochester page no longer includes discoverers
        authors = ''

        # now assemble this for the website, but only if it's after year 2000
        #  (use other page as early authority, for simplicity).
        if date.year < 2000:
            continue
        # put an extra couple tests here, since mis-parsed magnitudes can be noticible
        if mag > 30:
            raise Exception('Misparsed: Mag too faint')
        if mag < 3.0:
            # 1987A was mag 4.5
            raise Exception('Misparsed: Mag too bright')
        dictentry = {'name':name, 'galaxy':gal, 'date':datestr,
                     'magnitude':mag, 'type':sntype, 'authors':authors}
        coords = ephem.Equatorial(np.deg2rad(snRA), np.deg2rad(snDec))
        dictentry['eqcoords'] = [round(snRA,6), round(snDec,6)]
        galcoords = ephem.Galactic(coords)
        dictentry['coords'] = [round(np.rad2deg(galcoords.lon),2), round(np.rad2deg(galcoords.lat),2)]
        SNe2.append(dictentry)
        jds2.append(date2jd(date))
    except Exception as e:
        if VERBOSE: print(('skipping',sn,rocd[sn],":",e))
print(f'adding {len(SNe2)} from rochester page')

#####################################
# Now pull the IAUC page info
#####################################

if VERBOSE: print('opening page.')
page = urllib.request.urlopen('http://www.cbat.eps.harvard.edu/lists/Supernovae.html').read().decode('utf8','ignore')
table = page.split('<pre>')[1].split('</pre>')[0]
entries = [remove_tags(row) for row in table.split('\n') if row]

if VERBOSE: print('parsing result')
SNe3 = []
jds3 = []
for entry in entries[:-1]:
    try:
        name = entry[:8].strip()
        if not name or name in ['(V843)','B Cas']:
            name = None
        else:
            # add the 'SN' prefix
            name = 'SN '+name
        gal = entry[8:25].strip()
        try:
            date = datetime.strptime(entry[25:35].strip(), '%Y %m %d')
            datestr = '{} {}, {}'.format( months[date.month], date.day, date.year)
        except ValueError:
            try:
                date = datetime.strptime(entry[25:35].strip(), '%Y %m')
                datestr = '{} {}'.format( months[date.month], date.year)
            except ValueError:
                date = datetime.strptime(entry[25:35].strip(), '%Y')
                datestr = '{}'.format(date.year)
        try:
            galRA = parse_ra(entry[37:44])
            galDec = parse_dec(entry[45:51])
        except:
            galRA, galDec = None, None
        try:
            mag = round(float(entry[64:68]),2)
        except:
            mag = None
        try:
            snRA = parse_ra(entry[87:98])
            snDec = parse_dec(entry[99:110])
        except:
            snRA, snDec = None, None
        sntype = entry[130:136].strip()
        if not sntype:
            sntype = None
        authors = entry[144:].strip()
        if not authors:
            authors = None
        # if name is not given, construct one out of the year
        if name == None:
            name = 'SN {}A'.format(date.year)
        dictentry = {'name':name, 'galaxy':gal, 'date':datestr,
                     'magnitude':mag, 'type':sntype, 'authors':authors}
        if snRA:
            coords = ephem.Equatorial(np.deg2rad(snRA), np.deg2rad(snDec))
            dictentry['eqcoords'] = [round(snRA,6), round(snDec,6)]
        elif galRA:
            coords = ephem.Equatorial(np.deg2rad(galRA), np.deg2rad(galDec))
            dictentry['eqcoords'] = [round(galRA,6), round(galDec,6)]
        galcoords = ephem.Galactic(coords)
        dictentry['coords'] = [round(np.rad2deg(galcoords.lon),2), round(np.rad2deg(galcoords.lat),2)]
        
        jds3.append(date2jd(date))
        SNe3.append(dictentry)
    except:
        if VERBOSE: print(('skipping',entry))
print(f'adding {len(SNe3)} from iauc page')

#####################################
# Now merge them
#####################################
allnames = [o['name'] for o in SNe]
for i,obj in enumerate(SNe2):
    if obj['name'] not in allnames:
        SNe.append(obj)
        jds.append( jds2[i] )
        if VERBOSE: print(('including',obj['name']))
allnames = [o['name'] for o in SNe]
for i,obj in enumerate(SNe3):
    if obj['name'] not in allnames:
        SNe.append(obj)
        jds.append( jds3[i] )
        if VERBOSE: print(('including',obj['name']))

# sort them by explosion date
jds = np.array(jds)
order = jds.argsort()
jds = jds[order]
sortedSNe = []
for i in order:
    sortedSNe.append( SNe[i] )
SNe = sortedSNe
# and, so that we can bin them, makes sure that there are no exactly
#  matched JDs (np.digitize requires true monotonicity)
for i in range(1,len(jds)):
    if jds[i] == jds[i-1]:
        jds[i] += 0.001

# create a list of timesteps of len n_tsteps with a reasonable number of SNe in each
#  take special care with first few, so that we get a clean pre-1900 range
trim_jds = list(set(jds))
trim_jds.sort()
timesteps = [trim_jds[0], trim_jds[4]]
x = list(range(len(trim_jds[5:])))
spline = UnivariateSpline(x,trim_jds[5:], s=1E5)
X = np.linspace(0,len(trim_jds[4:]),n_tsteps)
timesteps += spline(X).tolist()
timesteps = np.array([round(t,1) for t in timesteps])
timesteps[1] -= 5000 #just a quick cleanup

# include a string representing the year and month of each
datestrings = []
for i,t in enumerate(timesteps[:-1]):
    now = jd2gcal(0,t)
    next = jd2gcal(0,timesteps[i+1])
    ds = str(months[now[1]]).ljust(5) + str(now[2]).rjust(2) + str(now[0]).rjust(5) + " - " +\
         str(months[next[1]]).ljust(5) + str(next[2]).rjust(2) + str(next[0]).rjust(5)
    ds = ds.replace(' ', '&nbsp;') # use non-breaking space character so the HTML renders correctly
    datestrings.append( ds )
# create a timing array that includes all SNe to explode in a certain range
binned_jds = np.digitize( jds, timesteps )
explosions = [None]*max(binned_jds)
for i,jd in enumerate(jds):
    iexplode = binned_jds[i] - 1
    if not explosions[iexplode]:
        explosions[iexplode] = [i]
    else:
        explosions[iexplode].append(i)
    SNe[i]['bin'] = int(iexplode)

# verify that we got the page properly, and everything is good to go
#assert len(SNe) > 10000
# and write to file
print(f'writing {len(SNe)} to file')
# now write both the all_sne and the timing variables to file
s = json.dumps(SNe)
outfile = open(outf, 'w')
outfile.write('all_objs = \n')
outfile.write(s)
s = json.dumps(list(zip(explosions,datestrings)))
outfile.write('\ntiming_array = \n')
outfile.write(s)
outfile.close()
if VERBOSE: print('done!')
    
