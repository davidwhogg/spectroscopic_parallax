#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  2 11:10:48 2018

@author: eilers
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import scipy.optimize as op
import time
import pickle
from astropy.table import Column, Table, join, vstack, hstack
import sys
from astropy.io import fits
from sklearn.decomposition import PCA
from astropy import units as u
from astropy.coordinates import SkyCoord
import astropy.coordinates as coord
from mpl_toolkits.mplot3d import Axes3D
import corner


# -------------------------------------------------------------------------------
# plotting settings
# -------------------------------------------------------------------------------

matplotlib.rcParams['ytick.labelsize'] = 14
matplotlib.rcParams['xtick.labelsize'] = 14
fsize = 14

# -------------------------------------------------------------------------------
# open inferred labels
# -------------------------------------------------------------------------------

N = 45787
Kfold = 2
lam = 100
name = 'N{0}_lam{1}_K{2}_offset'.format(N, lam, Kfold)

print('loading new labels...')   
labels = Table.read('data/training_labels_new_{}_2.fits'.format(name), format = 'fits')    
labels.rename_column('ra_1', 'ra')
labels.rename_column('dec_1', 'dec')

# -------------------------------------------------------------------------------
# calculate cartesian coordinates
# -------------------------------------------------------------------------------           

spec_par = labels['spec_parallax'] * u.mas
distance = spec_par.to(u.parsec, equivalencies = u.parallax())

cs = coord.ICRS(ra = labels['ra'] * u.degree, 
                dec = labels['dec'] * u.degree, 
                distance = distance, 
                pm_ra_cosdec = labels['pmra'] * u.mas/u.yr, 
                pm_dec = labels['pmdec'] * u.mas/u.yr, 
                radial_velocity = labels['VHELIO_AVG'] *u.km/u.s)


#Galactocentric position of the Sun:
X_GC_sun_kpc = 8.    #[kpc]
Z_GC_sun_kpc = 0.025 #[kpc] (e.g. Juric et al. 2008)

#circular velocity of the Galactic potential at the radius of the Sun:
vcirc_kms = 220. #[km/s] (e.g. Bovy 2015)

#Velocity of the Sun w.r.t. the Local Standard of Rest (e.g. Schoenrich et al. 2009):
U_LSR_kms = 11.1  # [km/s]
V_LSR_kms = 12.24 # [km/s]
W_LSR_kms = 7.25  # [km/s]

#Galactocentric velocity of the Sun:
vX_GC_sun_kms = -U_LSR_kms           # = -U              [km/s]
vY_GC_sun_kms =  V_LSR_kms+vcirc_kms # = V+v_circ(R_Sun) [km/s]
vZ_GC_sun_kms =  W_LSR_kms           # = W               [km/s]

gc = coord.Galactocentric(galcen_distance = X_GC_sun_kpc*u.kpc,
                          galcen_v_sun = coord.CartesianDifferential([-vX_GC_sun_kms, vY_GC_sun_kms, vZ_GC_sun_kms] * u.km/u.s),
                          z_sun = Z_GC_sun_kpc*u.kpc)

galcen = cs.transform_to(gc)
xs, ys, zs = galcen.x.to(u.kpc), galcen.y.to(u.kpc), galcen.z.to(u.kpc)
vxs, vys, vzs = galcen.v_x, galcen.v_y, galcen.v_z

XS = np.vstack([xs, ys, zs, vxs, vys, vzs]).T.value
Xlimits = [[-30, 10], [-10, 30], [-20, 20], 
           [-200, 200], [-200, 200], [-200, 200]]
Xlabels = ['$x$', '$y$', '$z$', r'$v_x$', r'$v_y$', r'$v_z$']

d2d = np.sqrt(XS[:, 0] ** 2 + XS[:, 1] ** 2)
units = XS[:, 0:2] / d2d[:, None]
perps = np.zeros_like(units)
perps[:, 0] = units[:, 1]
perps[:, 1] = -units[:, 0]
vtans = np.sum(perps * XS[:, 3:5], axis=1)
R = np.sqrt(XS[:, 0] ** 2 + XS[:, 1] ** 2) # in cylindrical coordinates! # + XS[:, 2] ** 2)

# -------------------------------------------------------------------------------
# take open cluster
# -------------------------------------------------------------------------------

t = Table(names = ('cluster', 'RA', 'DEC', 'FE_H', 'distance', 'lat_name'), dtype=('S8', 'S8', 'S8', 'S16', 'f8', 'S8'))

# M67
clus = 'm67'
lat = 'M 67'
ra_clus_hms = '08:51:18'
dec_clus_dms = '+11:48:00'
distance = 0.857 #kpc (from Yakut et al. 2009)
feh_clus = '+0.01\pm 0.05'
t.add_row([clus, ra_clus_hms, dec_clus_dms, feh_clus, distance, lat])

# NGC 6791
clus = 'ngc6791'
lat = 'NGC 6791'
ra_clus_hms = '19:20:53.0' 
dec_clus_dms = '+37:46:18'
distance = 4.078
feh_clus = '+0.47\pm 0.07'
t.add_row([clus, ra_clus_hms, dec_clus_dms, feh_clus, distance, lat])

# NGC 6819
clus = 'ngc6819'
lat = 'NGC 6891'
ra_clus_hms = '19:41:18.0' 
dec_clus_dms = '+40:11:12'
distance = 2.2 #kpc
feh_clus = '+0.09\pm 0.03'
t.add_row([clus, ra_clus_hms, dec_clus_dms, feh_clus, distance, lat])

# M35
clus = 'm35'
lat = 'M 35'
ra_clus_hms = '06 08 54.0' 
dec_clus_dms = '+24 20 00'
distance = 0.85 #kpc
feh_clus = '-0.21\pm 0.10'
t.add_row([clus, ra_clus_hms, dec_clus_dms, feh_clus, distance, lat])

# M92
clus = 'm92'
lat = 'M 92'
ra_clus_hms = '17 17 07.39' 
dec_clus_dms = '+43 08 09.4'
distance = 8.2 #kpc
feh_clus = '-2.35\pm 0.05'
t.add_row([clus, ra_clus_hms, dec_clus_dms, feh_clus, distance, lat])

# M15
clus = 'm15'
lat = 'M 15'
ra_clus_hms = '21 29 58.33' 
dec_clus_dms = '+12 10 01.2'
distance = 10.3 #kpc
feh_clus = '-2.33\pm 0.02'
t.add_row([clus, ra_clus_hms, dec_clus_dms, feh_clus, distance, lat])

# M53
clus = 'm53'
lat = 'M 53'
ra_clus_hms = '13 12 55.25' 
dec_clus_dms = '+18 10 05.4'
distance = 17.9 #kpc
feh_clus = '-2.06\pm 0.09'
t.add_row([clus, ra_clus_hms, dec_clus_dms, feh_clus, distance, lat])

# M13
clus = 'm13'
lat = 'M 13'
ra_clus_hms = '16 41 41.634' 
dec_clus_dms = '+36 27 40.75'
distance = 6.8 #kpc
feh_clus = '-1.58\pm 0.04'
t.add_row([clus, ra_clus_hms, dec_clus_dms, feh_clus, distance, lat])

# M2
clus = 'm2'
lat = 'M 2'
ra_clus_hms = '21 33 27.02' 
dec_clus_dms = '-00 49 23.7'
distance = 10 #kpc
feh_clus = '-1.66\pm 0.07'
t.add_row([clus, ra_clus_hms, dec_clus_dms, feh_clus, distance, lat])

# M3
clus = 'm3'
lat = 'M 3'
ra_clus_hms = '13 42 11.62' 
dec_clus_dms = '+28 22 38.2'
distance = 10.4 #kpc
feh_clus = '-1.50\pm 0.05'
t.add_row([clus, ra_clus_hms, dec_clus_dms, feh_clus, distance, lat])

# M5
clus = 'm5'
lat = 'M 5'
ra_clus_hms = '15 18 33.22' 
dec_clus_dms = '+02 04 51.7'
distance = 7.5 #kpc
feh_clus = '-1.33\pm 0.02'
t.add_row([clus, ra_clus_hms, dec_clus_dms, feh_clus, distance, lat])

# M71
clus = 'm71'
lat = 'M 71'
ra_clus_hms = '19 53 46.49' 
dec_clus_dms = '+18 46 45.1'
distance = 4. #kpc
feh_clus = '-1.33\pm 0.02'
t.add_row([clus, ra_clus_hms, dec_clus_dms, feh_clus, distance, lat])

# M107
clus = 'm107'
lat = 'M 107'
ra_clus_hms = '16 32 31.86' 
dec_clus_dms = '-13 03 13.6'
distance = 6.4 #kpc
feh_clus = '-1.03\pm 0.02'
t.add_row([clus, ra_clus_hms, dec_clus_dms, feh_clus, distance, lat])

# M45 = Pleiades (no stars found)
clus = 'm45'
lat = 'M 45'
ra_clus_hms = '03 47 00.0' 
dec_clus_dms = '+24 07 00'
distance = 0.136 #kpc
feh_clus = '+0.03\pm 0.02'
t.add_row([clus, ra_clus_hms, dec_clus_dms, feh_clus, distance, lat])

# NGC 2158
clus = 'ngc2158'
lat = 'NGC 2158'
ra_clus_hms = '06 07 25.0' 
dec_clus_dms = '+24 05 48'
distance = 3.37 #kpc
feh_clus = '-0.28\pm 0.05'
t.add_row([clus, ra_clus_hms, dec_clus_dms, feh_clus, distance, lat])

# NGC 188
clus = 'ngc188'
lat = 'NGC 188'
ra_clus_hms = '00 48 26.0' 
dec_clus_dms = '+85 15 18'
distance = 1.66 #kpc
feh_clus = '-0.03\pm 0.04'
t.add_row([clus, ra_clus_hms, dec_clus_dms, feh_clus, distance, lat])

# NGC 6819
clus = 'ngc6819'
lat = 'NGC 6819'
ra_clus_hms = '00 48 26.0' 
dec_clus_dms = '+85 15 18'
distance = 1.66 #kpc
feh_clus = '+0.09\pm 0.03'
t.add_row([clus, ra_clus_hms, dec_clus_dms, feh_clus, distance, lat])

# NGC 7789
clus = 'ngc7789'
lat = 'NGC 7789'
ra_clus_hms = '23 57 24.0' 
dec_clus_dms = '+56 42 30'
distance = 2.33 #kpc
feh_clus = '+0.02\pm 0.04'
t.add_row([clus, ra_clus_hms, dec_clus_dms, feh_clus, distance, lat])

# NGC 2420
clus = 'ngc2420'
lat = 'NGC 2420'
ra_clus_hms = '07 38 23.0' 
dec_clus_dms = '+21 34 24'
distance = 2.5 #kpc
feh_clus = '-0.20\pm 0.06'
t.add_row([clus, ra_clus_hms, dec_clus_dms, feh_clus, distance, lat])

c = SkyCoord('{0} {1}'.format(ra_clus_hms, dec_clus_dms), unit=(u.hourangle, u.deg))
ra_clus = c.ra.deg
dec_clus = c.dec.deg

cut_clus = (abs(labels['ra'] - ra_clus) < 1) \
          * (abs(labels['dec'] - dec_clus) < 1) # not isotropic --> rectangle!

XS_clus = np.vstack([labels['ra'][cut_clus], labels['dec'][cut_clus], labels['spec_parallax'][cut_clus]]).T
Xlabels_clus = ['RA', 'DEC', r'$\varpi$']
fig = corner.corner(XS_clus, labels = Xlabels_clus, truths = [ra_clus, dec_clus, 1./distance])
fig.savefig('plots/corner_{}_varpi.pdf'.format(clus))

# -------------------------------------------------------------------------------
# plot for paper (3x2) histograms: Gaia vs. me (labeled by cluster name and metallicity)
# -------------------------------------------------------------------------------

cluster_list = ['m53', 'm107', 'm3', 'm5', 'ngc6791', 'm92']

fig, ax = plt.subplots(3, 2, figsize = (10, 15))
plt.subplots_adjust(wspace = 0.08, hspace = 0.25)
for i, clus in enumerate(cluster_list):    
    c = i % 3
    r = i % 2    
    k = t['cluster'] == clus
    
    coord = SkyCoord('{0} {1}'.format(t['RA'][k][0], t['DEC'][k][0]), unit=(u.hourangle, u.deg))
    ra_clus = coord.ra.deg
    dec_clus = coord.dec.deg
    cut_clus = (abs(labels['ra'] - ra_clus) < .8) \
          * (abs(labels['dec'] - dec_clus) < .8) 
          
    bins = np.linspace(-0.1, 1, 15)
    if c == 0:  
        bins = np.linspace(-0.1, 1, 18)
    ax[c, r].hist(labels['spec_parallax'][cut_clus], normed = True, bins = bins, histtype = 'step', lw = 3, color = 'k', label = 'spectroscopic parallax')
    ax[c, r].hist(labels['parallax'][cut_clus], normed = True, bins = bins, histtype = 'step', lw = 1, color = 'k', label = 'Gaia parallax')
    ax[c, r].tick_params(axis=u'both', direction='in', which='both')
    ax[c, r].legend(frameon = True)
    ax[c, r].axvline(1./t['distance'][k][0], linestyle = '--', color = '#929591', lw = 2)
    ax[c, r].set_title(r'{0}, $\rm [Fe/H] = {1}$'.format(t['lat_name'][k][0], t['FE_H'][k][0]), fontsize = 14)
    ax[c, r].set_xlabel(r'$\varpi$', fontsize = 14)
    ax[c, r].set_xlim(-0.1, 1.)
plt.savefig('plots/open_clusters/test_open_clusters_{}.pdf'.format(name))

# -------------------------------------------------------------------------------
# take Sagittarius region...
# -------------------------------------------------------------------------------

hdu = fits.open('data/Sgr_Candidate_in_Gaia.fits')
data_sgr = hdu[1].data

indices = np.arange(len(labels))     
xx = []              
for i in data_sgr['APOGEE_ID']:
    foo = labels['APOGEE_ID'] == i
    if np.sum(foo) == 1:
        xx.append(indices[foo][0])
xx = np.array(xx)

labels_sgr = labels[xx]

XS_sgr = np.vstack([labels_sgr['ra'], labels_sgr['dec'], labels_sgr['spec_parallax']]).T
Xlabels_sgr = ['RA', 'DEC', r'$\varpi$']
fig = corner.corner(XS_sgr, labels = Xlabels_sgr, plot_datapoints = True)
fig.savefig('plots/open_clusters/corner_sgr_varpi_{}.pdf'.format(name)) 

fig, ax = plt.subplots(1, 1, figsize = (8, 8))
ax.scatter(labels_sgr['RA'], labels_sgr['spec_parallax'], zorder = 20, color = '#363737', s = 20, label = 'spectroscopic parallax')
ax.scatter(labels_sgr['RA'], labels_sgr['parallax'], zorder = 10, color = "#95d0fc", s = 15, label = 'Gaia parallax')
ax.set_xlabel('RA', fontsize = 14)
ax.legend(frameon = True, fontsize = 14)
ax.set_ylabel(r'$\varpi$', fontsize = 14)    
ax.tick_params(axis=u'both', direction='in', which='both')
ax.axhline(1./20, linestyle = '--', color = '#929591')
ax.set_title('Sagittarius', fontsize = 14)         
plt.savefig('plots/open_clusters/sagittarius_ra_varpi_{}.pdf'.format(name)) 
plt.close()

plt.hist(1./labels_sgr['spec_parallax'], bins = np.linspace(-1000, 1000, 60), histtype = 'step', lw=3, color='k', label = 'spec. parallax')
plt.hist(1./labels_sgr['parallax'], bins = np.linspace(-1000, 1000, 50), histtype = 'step', lw=1, color='k', label = 'Gaia parallax')
plt.xlabel(r'distance [kpc]', fontsize = 14)
plt.xlim(-500, 500)
plt.axvline(20, linestyle = '--', color = '#929591')
plt.tick_params(axis=u'both', direction='in', which='both')
plt.legend(frameon = True, fontsize = 12)
plt.savefig('plots/open_clusters/hist_sgr_dist_{}.pdf'.format(name)) 
plt.close()

Q_spec = labels['spec_parallax'] * 10 ** (0.2 * labels['K'])/ 100.
Q_spec = labels_sgr['spec_parallax'] * 10 ** (0.2 * labels_sgr['K'])/ 100.
Q_spec_gaia = labels_sgr['parallax'] * 10 ** (0.2 * labels_sgr['K'])/ 100.
                        
plt.hist(labels_sgr['spec_parallax'], bins = np.linspace(-1, 1, 100), histtype = 'step', lw=3, color='k', label = 'spec. parallax')
plt.hist(labels_sgr['parallax'], bins = np.linspace(-1, 1, 100), histtype = 'step', lw=1, color='k', label = 'Gaia parallax')
plt.xlabel(r'$\varpi$ [mas]', fontsize = 14)
plt.xlim(-0.2, 0.2)
plt.axvline(1./20, linestyle = '--', color = '#929591')
plt.tick_params(axis=u'both', direction='in', which='both')
plt.legend(frameon = True, fontsize = 11)
plt.savefig('plots/open_clusters/sagittarius_parallax_{}.pdf'.format(name))                        
plt.close()
# -------------------------------------------------------------------------------'''
