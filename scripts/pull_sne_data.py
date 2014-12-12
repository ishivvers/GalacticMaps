'''
A script to scrape the up-to-date SN info from
http://www.cbat.eps.harvard.edu/lists/Supernovae.html
and format it properly.
'''

import urllib2, re, json, ephem
import numpy as np
from astro.iAstro import parse_ra, parse_dec, date2jd
from jdcal import jd2gcal
from datetime import datetime
from scipy.interpolate import UnivariateSpline

# outf = '/o/ishivvers/public_html/js/sne.json'
outf = 'sne.json'
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

print 'opening page.'
page = urllib2.urlopen('http://www.rochesterastronomy.org/snimages/sndateall.html').read().decode('utf8','ignore')
table = page.split('<pre>')[1].split('</pre>')[0].split('\n')

print 'parsing result'
for istart, row in enumerate(table):
    if ('R.A.' in row) & ('Decl.' in row):
        # pull out the header
        ira = row.index('R.A.')
        idec = row.index('Decl.')
        iobs = row.index('Earliest')
        ihost = row.index('Host')
        ityp = row.index('Type')
        imax = row.index('Max')
        break
SNe = []
jds = []
for row in table[istart+1:]:
    try:
        # get coords
        snRA = parse_ra( row[ira:].strip().split(' ',1)[0] )
        snDec = parse_dec( row[idec:].strip().split(' ',1)[0] )
        # get Gregorian and Julian discovery date
        date = datetime.strptime( row[iobs:].strip().split(' ',1)[0].split('.')[0], '%Y/%m/%d')
        datestr = '{} {}, {}'.format( months[date.month], date.day, date.year)
        # get the type, host, and max brightness
        sntype = row[ityp:].split(' ',1)[0]
        if sntype == 'unk':
            sntype = None
            raise Exception('not confirmed.')
        if sntype in ['LBV', 'LBV?']:
            raise Exception('not a sn')
        gal = row[ihost:ityp].strip()
        mag = round(float( row[imax:].strip().split(' ',1)[0].strip('*') ), 2 )
        name = row.split('"_self">')[1].split('</a>')[0]
        # some are bad:
        if name in ['PS1-14vd']:
            raise Exception('bullshit!')
        # add 'SN' if needed
        if re.search('^\d{4}.*', name) and 'Possible' not in name:
            name = 'SN '+name
        authors = row.split('</a>')[1].strip()

        # now assemble this for the website, but only if it's after year 2000
        #  (use other page as early authority, for simplicity).
        if date.year < 2000:
            continue
        dictentry = {'name':name, 'galaxy':gal, 'date':datestr,
                     'magnitude':mag, 'type':sntype, 'authors':authors}
        coords = ephem.Equatorial(np.deg2rad(snRA), np.deg2rad(snDec))
        dictentry['eqcoords'] = [round(snRA,6), round(snDec,6)]
        galcoords = ephem.Galactic(coords)
        dictentry['coords'] = [round(np.rad2deg(galcoords.lon),2), round(np.rad2deg(galcoords.lat),2)]
        SNe.append(dictentry)
        jds.append(date2jd(date))
    except:
        print 'skipping',row


#####################################
# Now pull the IAUC page info
#####################################

print 'opening page.'
page = urllib2.urlopen('http://www.cbat.eps.harvard.edu/lists/Supernovae.html').read().decode('utf8','ignore')
table = page.split('<pre>')[1].split('</pre>')[0]
entries = [remove_tags(row) for row in table.split('\n') if row]

print 'parsing result'
SNe2 = []
jds2 = []
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
        jds2.append(date2jd(date))
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
            
        SNe2.append(dictentry)
    except:
        print 'skipping',entry

#####################################
# Now merge them
#####################################
allnames = [o['name'] for o in SNe]
for i,obj in enumerate(SNe2):
    if obj['name'] not in allnames:
        SNe.append(obj)
        jds.append( jds2[i] )
        print 'including',obj['name']

# create a list of timesteps of len n_tsteps with a reasonable number of SNe in each
#  take special care with first few, so that we get a clean pre-1900 range
trim_jds = list(set(jds))
trim_jds.sort()
timesteps = [trim_jds[0], trim_jds[4]]
x = range(len(trim_jds[5:]))
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
print 'writing to file; found',len(SNe),'objects.'
# now write both the all_sne and the timing variables to file
s = json.dumps(SNe)
outfile = open(outf, 'w')
outfile.write('all_objs = \n')
outfile.write(s)
s = json.dumps(zip(explosions,datestrings))
outfile.write('\ntiming_array = \n')
outfile.write(s)
outfile.close()
print 'done!'
    
