Versions:
- 20231115 - updated to make consistent with NICERDAS 11a/HEASoft 6.32.1 (requires python version > 3.8)
- 20250217 - (AZ) updates for the latest heasoftpy (v1.5)


## Content
In this example we'll use the NICER ObsID 4142010107, an observation of Cyg X-3. The data is available in the [HEASARC NICER archive](https://heasarc.gsfc.nasa.gov/FTP/nicer/data/obs/2021_11//4142010107/).

**Note** that in order to run this notebook in clean state, you may have to remove custom parameter
files from `~/pfiles`

```python
import os
import glob
import matplotlib.pyplot as plt
from astropy.table import Table
from astropy.time import Time
from astropy.io import fits
import astropy.units as u
import astropy.utils as au

import heasoftpy as hsp
import xspec

# suppress unimportant unit warning in astropy
import warnings
warnings.filterwarnings('ignore', category=au.exceptions.AstropyWarning, append=True)

```

## Setup

We'll **assume** the user has downloaded the NICER observation directory for OBSID `4142010107` in a the same location as the notebook. If not, add `os.chdir(location)`, where `location` is the folder containing `4142010107`.

The directory `4142010107` contains the `xti`, `auxil` and `hk` directories containing the standard archived data for the observation.

The following cell will check if the obsID folder does not exist, it will download it.

To find the location of the data, you can use [astroquery.heasarc](https://astroquery.readthedocs.io/en/latest/heasarc/heasarc.html)
or the [Xamin web interface](https://heasarc.gsfc.nasa.gov/xamin/).

```python

# downnload the data
nicerobsID = '4142010107'
if not os.path.exists(nicerobsID):
    os.system("wget -q -nH -r -l0 -c -N -np -R 'index*' -erobots=off --retr-symlinks --cut-dirs=5 "
              f"https://heasarc.gsfc.nasa.gov/FTP/nicer/data/obs/2021_11/{nicerobsID}/")

```

```python
nicerdatadir = os.getcwd()
obsdir = os.path.join(nicerdatadir, nicerobsID)

# place cleaned output in a separate directory
outdir =  os.path.join(nicerobsID + '_out')

```

```python
# # if outdir doesn't exist, create it
if not os.path.exists(outdir):
    os.makedirs(outdir, exist_ok=True)
    print(f'Created {outdir}')

# copy the mkf file from the observation folder
mkf = glob.glob(f'{obsdir}/auxil/*mkf')[0]
```

## Geomagnetic data 

First, download the geomagnetic data (used to estimate background) using  ``nigeodown`` (see https://heasarc.gsfc.nasa.gov/docs/nicer/analysis_threads/geomag/)

```python
# set the GEOMAG_PATH environment variable

os.environ['GEOMAG_PATH'] = os.path.join(nicerdatadir, 'geomag')

nigeodown = hsp.HSPTask('nigeodown')
res = nigeodown(clobber='yes')
if res.returncode == 0:
    print(f'Successfully downloaded geomagnetic quantities to {os.environ["GEOMAG_PATH"]}')
else:
    print(f'Could not download geomag quantities to {os.environ["GEOMAG_PATH"]}')
    print(res.stdout)
```

## Dating Processing

Use ``nicerl2`` to process your NICER observation.  We'll put the output from nicerl2 in an output directory (``outdir``, defined above) separate from the input directory

```python
tstart = Time.now()
```

```python
print(f'Start nicerl2 at: {tstart.iso[:19]}')
nicerl2 = hsp.HSPTask('nicerl2')

nicerl2.clobber="yes"
# add the KP values to the mkf file during nicerl2 processing
nicerl2.geomag_path=os.environ['GEOMAG_PATH']
nicerl2.geomag_columns = 'FILTCOLUMNS'
nicerl2.filtcolumns = 'NICERV5'
nicerl2.indir = nicerobsID
nicerl2.cldir = outdir

resl2 = nicerl2(noprompt=True)

tend = Time.now()
print(f'End at: {tend.iso[:19]}')
print(f'nicerl2 took: {(tend.mjd-tstart.mjd)*86400:.1f} seconds')

if resl2.returncode == 0:
    print('nicerl2 completed successfully')
else:
    print('PROBLEM running nicerl2', end='\n\n')
    print(resl2.output)

```

## Extract Products

The Recommended way to extract products from cleaned events file: use ``nicerl3-spect`` and ``nicerl3-lc``

### Running ``nicerl3-spect``
Use the ``scorpeon`` background model to create an estimated NICER background spectrum for the observation.  For simplicity we'll use the ``scorpeon`` model to create a background file that can be subtracted from the gross source spectrum

```python
nicerl3spect = hsp.HSPTask('nicerl3-spect')

nicerl3spect.cldir = outdir
nicerl3spect.indir = outdir
nicerl3spect.clobber = True
nicerl3spect.bkgmodeltype  = 'scorpeon'
nicerl3spect.format = 'file'
nicerl3spect.bkgformat = 'file'
nicerl3spect.mkfile = mkf

print(f'Start nicerl3-spect at: {tstart.iso[:19]}')


resl3s = nicerl3spect(noprompt=True)
if resl3s.returncode == 0:
    print('nicerl3-spect completed successfully')
else:
    print('PROBLEM running nicerl3-spect', end='\n\n')
    print(f'Return code = {resl3s.returncode}')
    print(resl3s.stdout)

```

### Running ``nicerl3-lc``

This creates a gross source lightcurve (no background subtraction) with a ``timebin = 10`` seconds in the PI channel range 30-800 (roughly 0.3 - 8 keV).

```python
nicerl3lc = hsp.HSPTask('nicerl3-lc')

nicerl3lc.indir = outdir
nicerl3lc.cldir = outdir
nicerl3lc.mkfile = mkf
nicerl3lc.clobber = True
nicerl3lc.bkgmodeltype  = 'scorpeon'
nicerl3lc.format = 'script'
nicerl3lc.pirange = '30:800'
nicerl3lc.timebin = 10
nicerl3lc.bkgmodeltype = 'sw'

print(f'Start nicerl3-lc at: {tstart.iso[:19]}')

resl3l = nicerl3lc()
if resl3s.returncode == 0:
    print('nicerl3-lc completed successfully')
else:
    print('PROBLEM running nicerl3-lc', end='\n\n')
    print(f'Return code = {resl3l.returncode}', end='\n\n')
    print(resl3l.stdout)

```

## Analyzing NICER spectra

```python
# change directory to outputdir
print(f'Changing directory to {outdir}')
os.chdir(outdir)

# get the rmf & arf
rmf = f'ni{nicerobsID}mpu7.rmf'
arf = f'ni{nicerobsID}mpu7.arf'

# get the source (sr) and background (bg) spectra
src = f'ni{nicerobsID}mpu7_sr.pha'
bkg = f'ni{nicerobsID}mpu7_bg.pha'

```

```python
xspec.AllData.clear()
spec = xspec.Spectrum(src)
spec.response = rmf
spec.response.arf = arf
spec.background = bkg
spec.ignore('0.0-0.3, 10.0-**')
```

```python
# define a simple model and fit it to the data

model = xspec.Model('wabs*bknpow')
#xspec.Fit.nIterations = 30

xspec.Fit.perform()
```

```python
%matplotlib inline
xspec.Plot.device='/null'
xspec.Plot.xAxis='keV'
xspec.Plot('lda')
cr=xspec.Plot.y()
crerr = xspec.Plot.yErr()
en = xspec.Plot.x()
enwid = xspec.Plot.xErr()
mop = xspec.Plot.model()
target = fits.open(spec.fileName)[1].header['OBJECT']


fig = plt.figure(figsize=[8,6])
plt.ylabel('Cts/s/keV', fontsize=12)
plt.xlabel('Energy (keV)', fontsize=12)
plt.title('Target = '+target+' OBSID = '+nicerobsID+' wabs*bknpow', fontsize=12)
plt.yscale('log')
plt.xscale('log')
plt.errorbar(en, cr, xerr=enwid, yerr=crerr, fmt='k.', alpha=0.2)
plt.plot(en, mop,'r-')
```

## Plot the lightcurve

```python
%matplotlib inline

lcfile = f'ni{nicerobsID}mpu7_sr.lc'
lcbkgfile = f'ni{nicerobsID}mpu7_bg.lc'
lctab = Table.read(lcfile,hdu='RATE')

#fig =subplots(1,1,figsize=[10,6])
plot(lctab['TIME'], lctab['RATE'],'.')
tmp = xlabel(f"MET - {lctab.meta['TSTART']}")
tmp = ylabel('Counts/s/52FPM')
```

