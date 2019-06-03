#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug  6 13:13:17 2018

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
from mpl_toolkits.axes_grid1.axes_divider import make_axes_locatable
from mpl_toolkits.axes_grid1.colorbar import colorbar


# -------------------------------------------------------------------------------
# plotting settings
# -------------------------------------------------------------------------------

matplotlib.rcParams['ytick.labelsize'] = 14
matplotlib.rcParams['xtick.labelsize'] = 14
matplotlib.rc('text', usetex=True)
fsize = 14
figsize = (8, 4.5)


# -------------------------------------------------------------------------------
# open inferred labels
# -------------------------------------------------------------------------------

#N = 45787
#Kfold = 2
#lam = 30
#name = 'N{0}_lam{1}_K{2}_parallax'.format(N, lam, Kfold)

N = 44784
Kfold = 2
lam = 30
name = 'N{0}_lam{1}_K{2}_offset0.0483_parallax'.format(N, lam, Kfold)

print('loading new labels...')   
labels = Table.read('data/training_labels_new_{}.fits'.format(name), format = 'fits')    
labels.rename_column('ra_1', 'ra')
labels.rename_column('dec_1', 'dec')

cut_jk = (labels['J'] - labels['K']) < (0.4 + 0.45 * labels['bp_rp'])
cut_hw2 = (labels['H'] - labels['w2mpro']) > -0.05
labels = labels[cut_jk * cut_hw2]

# -------------------------------------------------------------------------------
# Figure 1
# -------------------------------------------------------------------------------

# line parameters
x = np.linspace(0, 8, 10)
y1 = 0.4 + 0.45 * x
y2 = -0.05 + 0. * x

bprplim = (0.5, 6.0)
jklim = (0.2, 2.7)
hw2lim = (-0.1, 1.3)

cm = 'viridis_r'
fig, ax = plt.subplots(1, 2, figsize = figsize)
ax[0].scatter(labels['bp_rp'], labels['J']-labels['K'], c = labels['LOGG'], cmap = cm, vmin = 0, vmax = 2.2, rasterized = True, s = 10, alpha = .5)
sc = ax[1].scatter(labels['bp_rp'], labels['H']-labels['w2mpro'], c = labels['LOGG'], cmap = cm, vmin = 0, vmax = 2.2, rasterized = True, s = 10, alpha = .5)
ax[0].set_xlabel(r'$\rm B_P-R_p$', fontsize = fsize)
ax[1].set_xlabel(r'$\rm B_P-R_p$', fontsize = fsize)
ax[0].set_ylabel(r'$\rm J-K$', fontsize = fsize)
ax[1].set_ylabel(r'$\rm H-W_2$', fontsize = fsize)
ax[0].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[1].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
fig.subplots_adjust(right = 0.8)
cbar_ax = fig.add_axes([1, 0.15, 0.03, 0.82])
cb = fig.colorbar(sc, cax=cbar_ax)
cb.set_label(r'$\log g$', fontsize = fsize)
plt.tight_layout()
ax[0].set_xlim(bprplim)
ax[0].set_ylim(jklim)
ax[1].set_xlim(bprplim)
ax[1].set_ylim(hw2lim)
ax[0].plot(x, y1, linestyle= '-', color = '0.6')
ax[1].plot(x, y2, linestyle= '-', color = '0.6')
plt.savefig('paper/parent_sample.pdf', pad_inches=.2, bbox_inches = 'tight')

# -------------------------------------------------------------------------------
# Figure 2
# -------------------------------------------------------------------------------

cut_vis = labels['visibility_periods_used'] >= 8    
cut_par = labels['parallax_error'] < 0.1            
cut_cal = (labels['astrometric_chi2_al'] / np.sqrt(labels['astrometric_n_good_obs_al']-5)) <= 35         
train = cut_vis * cut_par * cut_cal  
best = train * (labels['parallax_over_error'] >= 20)

fig, ax = plt.subplots(1, 2, figsize = figsize)
ax[0].scatter(labels[train]['bp_rp'], labels[train]['J']-labels[train]['K'], c = labels[train]['LOGG'], cmap = cm, vmin = 0, vmax = 2.2, rasterized = True, s = 10, alpha = .5)
ax[1].scatter(labels[train]['bp_rp'], labels[train]['H']-labels[train]['w2mpro'], c = labels[train]['LOGG'], cmap = cm, vmin = 0, vmax = 2.2, rasterized = True, s = 10, alpha = .5)
ax[0].set_xlabel(r'$\rm B_P-R_p$', fontsize = fsize)
ax[1].set_xlabel(r'$\rm B_P-R_p$', fontsize = fsize)
ax[0].set_ylabel(r'$\rm J-K$', fontsize = fsize)
ax[1].set_ylabel(r'$\rm H-W_2$', fontsize = fsize)
ax[0].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[1].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
fig.subplots_adjust(right = 0.8)
cbar_ax = fig.add_axes([1, 0.15, 0.03, 0.82])
cb = fig.colorbar(sc, cax=cbar_ax)
cb.set_label(r'$\log g$', fontsize = fsize)
plt.tight_layout()
ax[0].plot(x, y1, linestyle= '-', color = '0.6')
ax[1].plot(x, y2, linestyle= '-', color = '0.6')
ax[0].set_xlim(bprplim)
ax[0].set_ylim(jklim)
ax[1].set_xlim(bprplim)
ax[1].set_ylim(hw2lim)
plt.savefig('paper/training_sample.pdf', pad_inches=.2, bbox_inches = 'tight')

# -------------------------------------------------------------------------------
# Figure 3 (parallax vs. parallax for training and Gaia excellent, colored by SNR)
# -------------------------------------------------------------------------------

fig, ax = plt.subplots(1, 2, figsize = figsize, sharey = True)
sc = ax[0].scatter(labels['parallax'][train], labels['spec_parallax'][train], c = labels['SNR'][train], cmap = 'viridis_r', s = 10, vmin = 50, vmax = 1000, rasterized = True)
ax[1].scatter(labels['parallax'][best], labels['spec_parallax'][best], c = labels['SNR'][best], cmap = 'viridis_r', s = 10, vmin = 50, vmax = 1000, rasterized = True)
ax[0].set_xlabel(r'$\varpi^{\rm (a)}$', fontsize = fsize)
ax[1].set_xlabel(r'$\varpi^{\rm (a)}$', fontsize = fsize)
ax[0].set_ylabel(r'$\varpi^{\rm (sp)}$', fontsize = fsize)
ax[0].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[1].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
#ax[0].set_aspect('equal')
#ax[1].set_aspect('equal')
ax[0].plot(np.arange(-1, 3), np.arange(-1, 3), color = '0.6', linestyle = ':')
ax[1].plot(np.arange(-1, 3), np.arange(-1, 3), color = '0.6', linestyle = ':')
ax[0].set_xlim(-.35, 2)
ax[1].set_xlim(-.35, 2)
ax[0].set_ylim(-.35, 2)
ax[1].set_ylim(-.35, 2)
ax[0].set_title('training set', fontsize = fsize)
ax[1].set_title(r'$\varpi^{\rm (a)}/\sigma_{\varpi^{\rm (a)}} \geq 20$', fontsize = fsize)
fig.subplots_adjust(right = 0.8)
cbar_ax = fig.add_axes([1, 0.15, 0.03, 0.75])
cb = fig.colorbar(sc, cax=cbar_ax)
cb.set_label(r'$\rm S/N$', fontsize = fsize)
plt.tight_layout()
plt.savefig('paper/residuals.pdf', pad_inches=.2, bbox_inches = 'tight')

# alternative version for referee
fig, ax = plt.subplots(1, 3, figsize = (12, 4.5), sharey = True)
sc = ax[0].scatter(labels['parallax'], labels['spec_parallax'], c = labels['SNR'], cmap = 'viridis_r', s = 10, vmin = 50, vmax = 1000, rasterized = True)
ax[1].scatter(labels['parallax'][train], labels['spec_parallax'][train], c = labels['SNR'][train], cmap = 'viridis_r', s = 10, vmin = 50, vmax = 1000, rasterized = True)
ax[2].scatter(labels['parallax'][best], labels['spec_parallax'][best], c = labels['SNR'][best], cmap = 'viridis_r', s = 10, vmin = 50, vmax = 1000, rasterized = True)
ax[0].set_xlabel(r'$\varpi^{\rm (a)}$', fontsize = fsize)
ax[1].set_xlabel(r'$\varpi^{\rm (a)}$', fontsize = fsize)
ax[2].set_xlabel(r'$\varpi^{\rm (a)}$', fontsize = fsize)
ax[0].set_ylabel(r'$\varpi^{\rm (sp)}$', fontsize = fsize)
ax[0].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[1].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[2].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[0].plot(np.arange(-1, 3), np.arange(-1, 3), color = '0.6', linestyle = ':')
ax[1].plot(np.arange(-1, 3), np.arange(-1, 3), color = '0.6', linestyle = ':')
ax[2].plot(np.arange(-1, 3), np.arange(-1, 3), color = '0.6', linestyle = ':')
ax[0].set_xlim(-.35, 2)
ax[1].set_xlim(-.35, 2)
ax[2].set_xlim(-.35, 2)
ax[0].set_ylim(-.35, 2)
ax[1].set_ylim(-.35, 2)
ax[2].set_ylim(-.35, 2)
ax[0].set_title('parent sample', fontsize = fsize)
ax[1].set_title('training set', fontsize = fsize)
ax[2].set_title(r'$\varpi^{\rm (a)}/\sigma_{\varpi^{\rm (a)}} \geq 20$', fontsize = fsize)
fig.subplots_adjust(right = 0.8)
cbar_ax = fig.add_axes([1, 0.15, 0.03, 0.75])
cb = fig.colorbar(sc, cax=cbar_ax)
cb.set_label(r'$\rm S/N$', fontsize = fsize)
plt.tight_layout()
plt.savefig('paper/residuals_inclduing_parent_sample.pdf', pad_inches=.2, bbox_inches = 'tight')

# -------------------------------------------------------------------------------
# Figure 4 (parallax vs. parallax colored by logg, Teff, [Fe/H], H-W2)
# -------------------------------------------------------------------------------

fig, ax = plt.subplots(2, 2, figsize = (10, 8))
sc = ax[0, 0].scatter(labels['parallax'][train], labels['spec_parallax'][train], c = labels['TEFF'][train], cmap = 'viridis_r', s = 10, vmin = 3600, vmax = 4800, rasterized = True)
cb = fig.colorbar(sc, ax = ax[0, 0])#, shrink = .8)
cb.set_label(r'$T_{\rm eff}$', fontsize = fsize)
sc = ax[0, 1].scatter(labels['parallax'][train], labels['spec_parallax'][train], c = labels['LOGG'][train], cmap = 'viridis_r', s = 10, vmin = 0.1, vmax = 2.2, rasterized = True)
cb = fig.colorbar(sc, ax = ax[0, 1])#, shrink = .8)
cb.set_label(r'$\log g$', fontsize = fsize)
sc = ax[1, 0].scatter(labels['parallax'][train], labels['spec_parallax'][train], c = labels['FE_H'][train], cmap = 'viridis_r', s = 10, vmin = -1, vmax = .5, rasterized = True)
cb = fig.colorbar(sc, ax = ax[1, 0]) #, shrink = .8)
cb.set_label(r'$\rm [Fe/H]$', fontsize = fsize)
sc = ax[1, 1].scatter(labels['parallax'][train], labels['spec_parallax'][train], c = labels['H'][train] - labels['w2mpro'][train], cmap = 'viridis_r', s = 10, vmin = 0., vmax = 0.5, rasterized = True)
cb = fig.colorbar(sc, ax = ax[1, 1]) #, shrink = .9)
cb.set_label(r'$\rm H-W_{2}$', fontsize = fsize)
ax[0, 0].set_xlabel(r'$\varpi^{\rm (a)}$', fontsize = fsize)
ax[0, 0].set_ylabel(r'$\varpi^{\rm (sp)}$', fontsize = fsize)
ax[0, 1].set_xlabel(r'$\varpi^{\rm (a)}$', fontsize = fsize)
ax[0, 1].set_ylabel(r'$\varpi^{\rm (sp)}$', fontsize = fsize)
ax[1, 0].set_xlabel(r'$\varpi^{\rm (a)}$', fontsize = fsize)
ax[1, 0].set_ylabel(r'$\varpi^{\rm (sp)}$', fontsize = fsize)
ax[1, 1].set_xlabel(r'$\varpi^{\rm (a)}$', fontsize = fsize)
ax[1, 1].set_ylabel(r'$\varpi^{\rm (sp)}$', fontsize = fsize)
ax[0, 0].plot(np.arange(-1, 3), np.arange(-1, 3), color = '0.6', linestyle = ':')
ax[0, 1].plot(np.arange(-1, 3), np.arange(-1, 3), color = '0.6', linestyle = ':')
ax[1, 0].plot(np.arange(-1, 3), np.arange(-1, 3), color = '0.6', linestyle = ':')
ax[1, 1].plot(np.arange(-1, 3), np.arange(-1, 3), color = '0.6', linestyle = ':')
ax[0, 0].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[0, 1].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[1, 0].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[1, 1].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[0, 0].set_aspect('equal')
ax[0, 1].set_aspect('equal')
ax[1, 0].set_aspect('equal')
ax[1, 1].set_aspect('equal')
ax[0, 0].set_xlim(-.35, 2)
ax[0, 1].set_xlim(-.35, 2)
ax[1, 0].set_xlim(-.35, 2)
ax[1, 1].set_xlim(-.35, 2)
ax[0, 0].set_ylim(-.35, 2)
ax[0, 1].set_ylim(-.35, 2)
ax[1, 0].set_ylim(-.35, 2)
ax[1, 1].set_ylim(-.35, 2)
plt.tight_layout()
plt.savefig('paper/residuals_training.pdf')

# alternative with parent sample for referee
fig, ax = plt.subplots(2, 2, figsize = (10, 8))
sc = ax[0, 0].scatter(labels['parallax'], labels['spec_parallax'], c = labels['TEFF'], cmap = 'viridis_r', s = 10, vmin = 3600, vmax = 4800, rasterized = True)
cb = fig.colorbar(sc, ax = ax[0, 0])#, shrink = .8)
cb.set_label(r'$T_{\rm eff}$', fontsize = fsize)
sc = ax[0, 1].scatter(labels['parallax'], labels['spec_parallax'], c = labels['LOGG'], cmap = 'viridis_r', s = 10, vmin = 0.1, vmax = 2.2, rasterized = True)
cb = fig.colorbar(sc, ax = ax[0, 1])#, shrink = .8)
cb.set_label(r'$\log g$', fontsize = fsize)
sc = ax[1, 0].scatter(labels['parallax'], labels['spec_parallax'], c = labels['FE_H'], cmap = 'viridis_r', s = 10, vmin = -1, vmax = .5, rasterized = True)
cb = fig.colorbar(sc, ax = ax[1, 0]) #, shrink = .8)
cb.set_label(r'$\rm [Fe/H]$', fontsize = fsize)
sc = ax[1, 1].scatter(labels['parallax'], labels['spec_parallax'], c = labels['H'] - labels['w2mpro'], cmap = 'viridis_r', s = 10, vmin = 0., vmax = 0.5, rasterized = True)
cb = fig.colorbar(sc, ax = ax[1, 1]) #, shrink = .9)
cb.set_label(r'$\rm H-W_{2}$', fontsize = fsize)
ax[0, 0].set_xlabel(r'$\varpi^{\rm (a)}$', fontsize = fsize)
ax[0, 0].set_ylabel(r'$\varpi^{\rm (sp)}$', fontsize = fsize)
ax[0, 1].set_xlabel(r'$\varpi^{\rm (a)}$', fontsize = fsize)
ax[0, 1].set_ylabel(r'$\varpi^{\rm (sp)}$', fontsize = fsize)
ax[1, 0].set_xlabel(r'$\varpi^{\rm (a)}$', fontsize = fsize)
ax[1, 0].set_ylabel(r'$\varpi^{\rm (sp)}$', fontsize = fsize)
ax[1, 1].set_xlabel(r'$\varpi^{\rm (a)}$', fontsize = fsize)
ax[1, 1].set_ylabel(r'$\varpi^{\rm (sp)}$', fontsize = fsize)
ax[0, 0].plot(np.arange(-1, 3), np.arange(-1, 3), color = '0.6', linestyle = ':')
ax[0, 1].plot(np.arange(-1, 3), np.arange(-1, 3), color = '0.6', linestyle = ':')
ax[1, 0].plot(np.arange(-1, 3), np.arange(-1, 3), color = '0.6', linestyle = ':')
ax[1, 1].plot(np.arange(-1, 3), np.arange(-1, 3), color = '0.6', linestyle = ':')
ax[0, 0].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[0, 1].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[1, 0].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[1, 1].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[0, 0].set_aspect('equal')
ax[0, 1].set_aspect('equal')
ax[1, 0].set_aspect('equal')
ax[1, 1].set_aspect('equal')
ax[0, 0].set_xlim(-.35, 2)
ax[0, 1].set_xlim(-.35, 2)
ax[1, 0].set_xlim(-.35, 2)
ax[1, 1].set_xlim(-.35, 2)
ax[0, 0].set_ylim(-.35, 2)
ax[0, 1].set_ylim(-.35, 2)
ax[1, 0].set_ylim(-.35, 2)
ax[1, 1].set_ylim(-.35, 2)
plt.tight_layout()
plt.savefig('paper/residuals_parent.pdf')

# -------------------------------------------------------------------------------
# Figure 5 (12 stellar clusters, fairly narrow bins)
# -------------------------------------------------------------------------------

# run test_distance.py

# -------------------------------------------------------------------------------
# Figure 6 (plot res.x vs. lambda for A and B model, linear (!) Cannon: logg output)
# -------------------------------------------------------------------------------

# linear Cannon with logg, Teff, [Fe/H] for A or B model --> overplot on res.x is some sensible way (partial wavelength range?)!

f1 = open('optimization/opt_results_0_{}.pickle'.format(name), 'rb')
res1 = pickle.load(f1)
f1.close() 
f2 = open('optimization/opt_results_1_{}.pickle'.format(name), 'rb')
res2 = pickle.load(f2)
f2.close() 

hdulist = fits.open('./data/spectra/apStar-t9-2M00000002+7417074.fits')
header = hdulist[1].header
flux = hdulist[1].data[0]
start_wl = header['CRVAL1']
diff_wl = header['CDELT1']
val = diff_wl * (len(flux)) + start_wl
wl_full_log = np.arange(start_wl, val, diff_wl)
wl = [10**aval for aval in wl_full_log]

hdu = fits.open('data/linear_cannon.fits')
parameters = hdu[0].data

hdu = fits.open('data/all_flux_norm_parent.fits')
fluxes = hdu[0].data
gaps = (np.sum(fluxes.T, axis = 0)) == float(fluxes.T.shape[0])

fig, ax = plt.subplots(2, 1, figsize = (12, 12), sharex = True, sharey = True)
ax[0].fill_between(np.array(wl)[~gaps], abs(res1.x[9:])) #, drawstyle = 'steps-mid', lw = .8, color = 'k')
ax[1].fill_between(np.array(wl)[~gaps], abs(res2.x[9:])) #, drawstyle = 'steps-mid', lw = .8, color = 'k')
for i in range(1, 2):
    ax[0].fill_between(wl, abs(5 * parameters[:, i]), alpha = .5)
    ax[1].fill_between(wl, abs(5 * parameters[:, i]), alpha = .5)
ax[1].set_xlabel(r'$\lambda~\rm[{\AA}]$', fontsize = 14)
ax[0].set_xlim(min(np.array(wl)[~gaps]), max(np.array(wl)[~gaps]))
ax[0].set_ylim(0., 0.5)
ax[0].set_xlim(16700, 16900)
plt.savefig('paper/coefficients.pdf')

# -------------------------------------------------------------------------------
# Figure 7 (map of kinematics & abundances)
# -------------------------------------------------------------------------------

# 6 degree wegde in z
# patch colored by metallicty, opacity proportional to number of stars
# superimposed arrow color coded by v_z, opacity also proportional to number of stars

# run rotation_curve_uncertainties.py


# -------------------------------------------------------------------------------
# Figure 8
# -------------------------------------------------------------------------------

#apogee_table = fits.open('data/allStar-l31c.2.fits')
#apogee_data = apogee_table[1].data
#
#cmap = 'RdYlBu_r'
#fig, ax = plt.subplots(1, 1, figsize = (5, 5))
#plt.scatter(apogee_data['TEFF'], apogee_data['LOGG'], s = .5, color = '#929591', rasterized = True, alpha = .01)
#plt.scatter(labels['TEFF'], labels['LOGG'], c = labels['FE_H'], s = .5, cmap = cmap, rasterized = True, alpha = 1, vmin = -.8, vmax = .5)
#plt.xlim(5500, 3500)
#plt.ylim(3.8, -.2)
#plt.xlabel(r'$T_{\rm eff}$', fontsize = 14)
#plt.ylabel(r'$\log g$', fontsize = 14)
#plt.tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
#plt.savefig('paper/HRD.pdf')

# color-color diagram?
spec_par = labels['spec_parallax'] * u.mas
distance = spec_par.to(u.parsec, equivalencies = u.parallax())
abs_mag_G = labels['phot_g_mean_mag'] - 5 * np.log10(distance.value) + 5

cut_vis = labels['visibility_periods_used'] >= 8    
cut_par = labels['parallax_error'] < 0.1            
cut_cal = (labels['astrometric_chi2_al'] / np.sqrt(labels['astrometric_n_good_obs_al']-5)) <= 35         
train = cut_vis * cut_par * cut_cal  
best_gaia = train * (labels['parallax_over_error'] >= 20)
best = train * ((labels['spec_parallax']/labels['spec_parallax_err']) >= 10)
cut_feh = labels['FE_H'] > -100

# -------------------------------------------------------------------------------
# final catalog!
# -------------------------------------------------------------------------------

training_set = np.zeros((len(labels)), dtype = int)
training_set[train] = 1
sample = np.zeros((len(labels)), dtype = str)
Kfold = 2
sample_A = labels['random_index'] % Kfold == 0
sample_B = np.logical_not(sample_A)
sample[sample_A] = 'A'
sample[sample_B] = 'B'
tab = labels['APOGEE_ID', 'parallax', 'parallax_error', 'spec_parallax', 'spec_parallax_err'] #, 'training_set', 'sample']
tab['parallax'] = Column(np.round(tab['parallax'], 4))
tab['parallax_error'] = Column(np.round(tab['parallax_error'], 4))
tab['spec_parallax'] = Column(np.round(tab['spec_parallax'], 4))
tab['spec_parallax_err'] = Column(np.round(tab['spec_parallax_err'], 4))
tab.rename_column('APOGEE_ID', '2MASS_ID')
tab.rename_column('parallax', 'Gaia_parallax')
tab.rename_column('parallax_error', 'Gaia_parallax_err')
tab.add_column(Column(training_set), name = 'training_set')
tab.add_column(Column(sample), name = 'sample')
Table.write(tab, 'data/data_HoggEilersRix2018.fits', format = 'fits', overwrite = True)
Table.write(tab[:12], 'paper/data_HoggEilersRix2018_part.txt', format = 'latex', overwrite = True)

cm = 'viridis'
fig, ax = plt.subplots(1, 2, figsize = figsize)
sc = ax[0].scatter(labels['bp_rp'], abs_mag_G, c = labels['spec_parallax'] - labels['parallax'], cmap = cm, rasterized = True, vmin = -.1, vmax = .1, s = 5, alpha = .5)
ax[1].scatter(labels[train]['bp_rp'], abs_mag_G[train], c = labels['spec_parallax'][train] - labels['parallax'][train], cmap = cm, rasterized = True, vmin = -.1, vmax = .1, s = 5, alpha = .5)
ax[0].set_xlabel(r'$\rm B_P-R_p$', fontsize = fsize)
ax[1].set_xlabel(r'$\rm B_P-R_p$', fontsize = fsize)
ax[0].set_ylabel(r'$\rm absolute\,\,G\,\,magnitude$', fontsize = fsize)
#ax[1].set_ylabel(r'$\rm absolute G magnitude$', fontsize = fsize)
ax[0].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[1].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[0].set_title('parent sample', fontsize = fsize)
ax[1].set_title(r'training set', fontsize = fsize)
fig.subplots_adjust(right = 0.8)
cbar_ax = fig.add_axes([1, 0.15, 0.03, 0.8])
cb = fig.colorbar(sc, cax=cbar_ax)
cb.set_label(r'$\varpi^{(\rm sp)} - \varpi^{(\rm a)}$', fontsize = fsize)
plt.tight_layout()
ax[0].set_xlim(.5, 7)
ax[1].set_xlim(.5, 7)
ax[0].set_ylim(7, -4.2)
ax[1].set_ylim(7, -4.2)
plt.savefig('paper/CMD.pdf', pad_inches=.2, bbox_inches = 'tight')

cm = 'RdBu_r'
fig, ax = plt.subplots(1, 2, figsize = figsize)
#sc = ax[0].scatter(labels['bp_rp'][cut_feh], abs_mag_G[cut_feh], c = labels['FE_H'][cut_feh], cmap = cm, rasterized = True, vmin = -2, vmax = .6, s = 5, alpha = .5)
sc = ax[0].scatter(labels[best_gaia * cut_feh]['bp_rp'], abs_mag_G[best_gaia * cut_feh], c = labels['FE_H'][best_gaia * cut_feh], cmap = cm, rasterized = True, vmin = -2, vmax = .6, s = 5, alpha = .5)
ax[1].scatter(labels[best * cut_feh]['bp_rp'], abs_mag_G[best * cut_feh], c = labels['FE_H'][best * cut_feh], cmap = cm, rasterized = True, vmin = -2, vmax = .6, s = 5, alpha = .5)
ax[0].set_xlabel(r'$\rm B_P-R_p$', fontsize = fsize)
ax[1].set_xlabel(r'$\rm B_P-R_p$', fontsize = fsize)
ax[0].set_ylabel(r'$\rm absolute\,\,G\,\,magnitude$', fontsize = fsize)
#ax[1].set_ylabel(r'$\rm absolute G magnitude$', fontsize = fsize)
ax[0].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[1].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
#ax[0].set_title('parent sample', fontsize = fsize)
ax[0].set_title(r'training set', fontsize = fsize)
ax[0].set_title(r'$\varpi^{\rm (a)}/\sigma_{\varpi^{\rm (a)}} \geq 20$', fontsize = fsize)
ax[1].set_title(r'$\varpi^{\rm (sp)}/\sigma_{\varpi^{\rm (sp)}} \geq 10$', fontsize = fsize)
fig.subplots_adjust(right = 0.8)
cbar_ax = fig.add_axes([1, 0.15, 0.03, 0.76])
cb = fig.colorbar(sc, cax=cbar_ax)
cb.set_label(r'$\rm [Fe/H]$', fontsize = fsize)
plt.tight_layout()
ax[0].set_xlim(.5, 4.5)
ax[1].set_xlim(.5, 4.5)
ax[0].set_ylim(4.5, -4.2)
ax[1].set_ylim(4.5, -4.2)
plt.savefig('paper/CMD4.pdf', pad_inches=.2, bbox_inches = 'tight')

hdu = fits.open('plots/open_clusters/M71members')
mem = Table(hdu[1].data)
xx = join(mem, labels, join_type = 'inner', keys = 'APOGEE_ID')

fig, ax = plt.subplots(1, 2, figsize = figsize)
sc = ax[0].scatter(labels['spec_parallax'] - labels['parallax'], labels['MEANFIB'], rasterized = True, s = 5, alpha = .2)
ax[1].scatter(labels['spec_parallax'][train] - labels['parallax'][train], labels['MEANFIB'][train], rasterized = True, s = 5, alpha = .2)
ax[0].scatter(xx['spec_parallax_2'] - xx['parallax_2'], xx['MEANFIB_2'], rasterized = True, s = 15, alpha = 1, color = 'r')
ax[1].scatter(xx['spec_parallax_2'] - xx['parallax_2'], xx['MEANFIB_2'], rasterized = True, s = 15, alpha = 1, color = 'r', label = 'M71')
ax[0].set_xlabel(r'$\varpi^{(\rm sp)}-\varpi^{(\rm a)}$', fontsize = fsize)
ax[1].set_xlabel(r'$\varpi^{(\rm sp)}-\varpi^{(\rm a)}$', fontsize = fsize)
ax[0].set_ylabel(r'mean fiber number', fontsize = fsize)
ax[0].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[1].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[0].set_title('parent sample', fontsize = fsize)
ax[1].set_title(r'training set', fontsize = fsize)
ax[0].set_xlim(-.5, .5)
ax[1].set_xlim(-.5, .5)
ax[1].legend()
plt.savefig('plots/fiber1.pdf', pad_inches=.2, bbox_inches = 'tight')

distance_xx = (xx['spec_parallax_2']*u.mas).to(u.parsec, equivalencies = u.parallax())

fig, ax = plt.subplots(1, 2, figsize = figsize)
sc = ax[0].scatter(distance/1000., labels['MEANFIB'], rasterized = True, s = 5, alpha = .2)
ax[1].scatter(distance[train]/1000., labels['MEANFIB'][train], rasterized = True, s = 5, alpha = .2)
ax[0].scatter(distance_xx/1000., xx['MEANFIB_2'], rasterized = True, s = 15, alpha = 1, color = 'r')
ax[1].scatter(distance_xx/1000., xx['MEANFIB_2'], rasterized = True, s = 15, alpha = 1, color = 'r', label = 'M71')
ax[0].set_xlabel(r'$d\rm\,[kpc]$', fontsize = fsize)
ax[1].set_xlabel(r'$d\rm\,[kpc]$', fontsize = fsize)
ax[0].set_ylabel(r'mean fiber number', fontsize = fsize)
ax[0].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[1].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[0].set_title('parent sample', fontsize = fsize)
ax[1].set_title(r'training set', fontsize = fsize)
ax[1].legend()
ax[0].set_xlim(0, 20)
ax[1].set_xlim(0, 20)
plt.savefig('plots/fiber2.pdf', pad_inches=.2, bbox_inches = 'tight')

fig, ax = plt.subplots(1, 2, figsize = figsize)
sc = ax[0].scatter(labels['spec_parallax'] - labels['parallax'], labels['SNR'], rasterized = True, s = 5, alpha = .2)
ax[1].scatter(labels['spec_parallax'][train] - labels['parallax'][train], labels['SNR'][train], rasterized = True, s = 5, alpha = .2)
ax[0].scatter(xx['spec_parallax_2'] - xx['parallax_2'], xx['SNR_2'], rasterized = True, s = 15, alpha = 1, color = 'r')
ax[1].scatter(xx['spec_parallax_2'] - xx['parallax_2'], xx['SNR_2'], rasterized = True, s = 15, alpha = 1, color = 'r', label = 'M71')
ax[0].set_xlabel(r'$\varpi^{(\rm sp)}-\varpi^{(\rm a)}$', fontsize = fsize)
ax[1].set_xlabel(r'$\varpi^{(\rm sp)}-\varpi^{(\rm a)}$', fontsize = fsize)
ax[0].set_ylabel(r'S/N', fontsize = fsize)
ax[0].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[1].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[0].set_title('parent sample', fontsize = fsize)
ax[1].set_title(r'training set', fontsize = fsize)
ax[0].set_xlim(-.5, .5)
ax[1].set_xlim(-.5, .5)
ax[1].legend()
plt.savefig('plots/systematics1.pdf', pad_inches=.2, bbox_inches = 'tight')

fig, ax = plt.subplots(1, 2, figsize = figsize)
sc = ax[0].scatter(labels['spec_parallax'] - labels['parallax'], labels['LOGG'], rasterized = True, s = 5, alpha = .2)
ax[1].scatter(labels['spec_parallax'][train] - labels['parallax'][train], labels['LOGG'][train], rasterized = True, s = 5, alpha = .2)
ax[0].scatter(xx['spec_parallax_2'] - xx['parallax_2'], xx['LOGG_2'], rasterized = True, s = 15, alpha = 1, color = 'r')
ax[1].scatter(xx['spec_parallax_2'] - xx['parallax_2'], xx['LOGG_2'], rasterized = True, s = 15, alpha = 1, color = 'r', label = 'M71')
ax[0].set_xlabel(r'$\varpi^{(\rm sp)}-\varpi^{(\rm a)}$', fontsize = fsize)
ax[1].set_xlabel(r'$\varpi^{(\rm sp)}-\varpi^{(\rm a)}$', fontsize = fsize)
ax[0].set_ylabel(r'$\log g$', fontsize = fsize)
ax[0].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[1].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[0].set_title('parent sample', fontsize = fsize)
ax[1].set_title(r'training set', fontsize = fsize)
ax[0].set_xlim(-.5, .5)
ax[1].set_xlim(-.5, .5)
ax[1].legend()
plt.savefig('plots/systematics2.pdf', pad_inches=.2, bbox_inches = 'tight')

N = len(labels)
fehrank = np.zeros(N)
fehrank[np.argsort(labels['FE_H'])] = np.arange(N)

fig, ax = plt.subplots(1, 2, figsize = figsize)
sc = ax[0].scatter(labels['spec_parallax'] - labels['parallax'], labels['FE_H'], rasterized = True, s = 5, alpha = .2)
ax[1].scatter(labels['spec_parallax'][train] - labels['parallax'][train], labels['FE_H'][train], rasterized = True, s = 5, alpha = .2)
ax[0].scatter(xx['spec_parallax_2'] - xx['parallax_2'], xx['FE_H_2'], rasterized = True, s = 15, alpha = 1, color = 'r')
ax[1].scatter(xx['spec_parallax_2'] - xx['parallax_2'], xx['FE_H_2'], rasterized = True, s = 15, alpha = 1, color = 'r', label = 'M71')
ax[0].set_xlabel(r'$\varpi^{(\rm sp)}-\varpi^{(\rm a)}$', fontsize = fsize)
ax[1].set_xlabel(r'$\varpi^{(\rm sp)}-\varpi^{(\rm a)}$', fontsize = fsize)
ax[0].set_ylabel(r'$\rm [Fe/H]$', fontsize = fsize)
ax[0].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[1].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[0].set_title(r'parent sample', fontsize = fsize)
ax[1].set_title(r'training set', fontsize = fsize)
ax[0].set_xlim(-.5, .5)
ax[1].set_xlim(-.5, .5)
ax[0].set_ylim(-2., .7)
ax[1].set_ylim(-2., .7)
#ax[1].legend()
plt.savefig('plots/systematics3.pdf', pad_inches=.2, bbox_inches = 'tight')
    
# -------------------------------------------------------------------------------'''
# plot for referee: data censoring
# -------------------------------------------------------------------------------

hdu = fits.open('data/training_labels_parent.fits')
labels_all = Table(hdu[1].data)
offset = 0.0483 
labels_all['parallax'] += offset 

bins = np.linspace(-.5, 1.5, 70)
fig, ax = plt.subplots(1, 3, figsize = (15, 5))
ax[0].hist(labels_all['parallax'][np.isfinite(labels_all['parallax']) == True], histtype='step', bins = bins, label = 'all RGB stars', lw = 2)
ax[0].hist(labels['parallax'][np.isfinite(labels['parallax']) == True], histtype='step', bins = bins, label = 'parent sample', lw = 2)
ax[0].hist(labels['parallax'][train], histtype='step', bins = bins, label = 'training set', lw = 2)
ax[0].legend(frameon = True, fontsize = fsize)
ax[0].set_xlabel(r'$\varpi^{\rm (a)}$', fontsize = fsize)
ax[0].set_ylabel('counts', fontsize = fsize)

bins2 = np.linspace(0, 1500, 70)
ax[1].hist(labels_all['SNR'], histtype='step', bins = bins2, lw = 2)
ax[1].hist(labels['SNR'], histtype='step', bins = bins2, lw = 2)
ax[1].hist(labels['SNR'][train], histtype='step', bins = bins2, lw = 2)
ax[1].set_xlabel(r'SNR', fontsize = fsize)

bins2 = np.linspace(0, 2.2, 70)
ax[2].hist(labels_all['LOGG'], histtype='step', bins = bins2, lw = 2)
ax[2].hist(labels['LOGG'], histtype='step', bins = bins2, lw = 2)
ax[2].hist(labels['LOGG'][train], histtype='step', bins = bins2, lw = 2)
ax[2].set_xlabel(r'$\log g$', fontsize = fsize)

ax[0].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[1].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
ax[2].tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')

plt.savefig('paper/censoring_data.pdf', pad_inches=.2, bbox_inches = 'tight')


# -------------------------------------------------------------------------------
# plot for referee: influence of parallax offset
# -------------------------------------------------------------------------------

N = 44784
Kfold = 2
lam = 30
name = 'N{0}_lam{1}_K{2}_offset0.0483_parallax'.format(N, lam, Kfold)

print('loading new labels...')   
labels = Table.read('data/training_labels_new_{}.fits'.format(name), format = 'fits')    
labels.rename_column('ra_1', 'ra')
labels.rename_column('dec_1', 'dec')

cut_jk = (labels['J'] - labels['K']) < (0.4 + 0.45 * labels['bp_rp'])
cut_hw2 = (labels['H'] - labels['w2mpro']) > -0.05
labels = labels[cut_jk * cut_hw2]

# -------------------------------------------------------------------------------
# plot for referee: coefficient vector
# -------------------------------------------------------------------------------

fig, ax = plt.subplots(1, 1, figsize = (10, 5))

xlabels = ['1', r'$G$', r'$G_{\rm BP}$', r'$G_{\rm RP}$', r'$J$', r'$H$', r'$K$', r'$W_1$', r'$W_2$']
x = [0, 1, 2, 3, 4, 5, 6, 7, 8]
name = 'N44784_lam30_K2_offset0.0483_parallax'

for run in range(0, 5):
    k = 0
    f = open('optimization/opt_results_{0}_{1}_run{2}.pickle'.format(k, name, run), 'rb')
    res = pickle.load(f)
    f.close()  
    if run == 0:
        ax.plot(x, res.x[:9], color = 'k', lw = .8, label = 'A')
    else:    
        ax.plot(x, res.x[:9], color = 'k', lw = .8)

    
    k = 1
    f = open('optimization/opt_results_{0}_{1}_run{2}.pickle'.format(k, name, run), 'rb')
    res = pickle.load(f)
    f.close()     
    if run == 0:
        ax.plot(x, res.x[:9], color = 'r', lw = .8, label = 'B')
    else:    
        ax.plot(x, res.x[:9], color = 'r', lw = .8)
        
ax.tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
plt.xticks(x, xlabels, fontsize = 18)
plt.ylabel(r'$\hat{\theta}$', fontsize = 18)
plt.legend(frameon = True, fontsize = 18)
plt.savefig('paper/coefficients.pdf', pad_inches=.2, bbox_inches = 'tight')


# -------------------------------------------------------------------------------
# plot for referee: comparison to other data
# -------------------------------------------------------------------------------

schultheis = Table.read('data/Schultheis2014.txt', format = 'ascii', header_start = 0)
matches = join(schultheis, labels, keys='APOGEE_ID')

spec_par_match = matches['spec_parallax'] * u.mas
distance_match = spec_par_match.to(u.parsec, equivalencies = u.parallax())

diff = np.log(matches['Dis']) - np.log(distance_match.value/1000.)
offset = np.median(diff)
scatter = np.percentile(diff, 84) - np.percentile(diff, 16)
print(offset, scatter)

chi2 = (distance_match.value/1000. - matches['Dis']) ** 2 / (matches['e_Dis']/100. * matches['Dis'])**2

fsize = 16
fig, ax = plt.subplots(1, 1, figsize = (8, 7))
plt.plot([-1, 50], [-1, 50], linestyle = '--', color = '#929591')
sc = plt.scatter(np.log(matches['Dis']), np.log(distance_match.value/1000.), c = matches['LOGG'], cmap = cm, vmin = 0, vmax = 2.2, s = 20)
#plt.errorbar(matches['Dis'], distance_match.value/1000., xerr = matches['e_Dis']/100. * matches['Dis'], fmt = 'o', alpha = .3)
cb = fig.colorbar(sc)
cb.set_label(r'$\log g$', fontsize = fsize)
ax.tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
plt.xlim(-.5, 4)
plt.ylim(-.5, 4)
plt.xlabel(r'$\ln d~$[kpc] (Schultheis+2014)', fontsize = fsize)
plt.ylabel(r'$\ln d~$[kpc] (Hogg, Eilers, Rix 2018)', fontsize = fsize)
plt.savefig('paper/comparison_schultheis.pdf', pad_inches=.2, bbox_inches = 'tight')



queiroz = fits.open('data/match_queiroz_HER.fits')
matches = queiroz[1].data
spec_par_match = matches['spec_parallax'] * u.mas
distance_match = spec_par_match.to(u.parsec, equivalencies = u.parallax())


fsize = 16
fig, ax = plt.subplots(1, 1, figsize = (8, 7))
plt.plot([-1, 50], [-1, 50], linestyle = '--', color = '#929591')
sc = plt.scatter(np.log(matches['BPG_meandist']), np.log(distance_match.value/1000.), c = matches['LOGG'], cmap = cm, vmin = 0, vmax = 2.2, s = 10)
#plt.errorbar(matches['Dis'], distance_match.value/1000., xerr = matches['e_Dis']/100. * matches['Dis'], fmt = 'o', alpha = .3)
cb = fig.colorbar(sc)
cb.set_label(r'$\log g$', fontsize = fsize)
ax.tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
plt.xlim(-.5, 4)
plt.ylim(-.5, 4)
plt.xlabel(r'$\ln d~$[kpc] (Queiroz et al. 2018)', fontsize = fsize)
plt.ylabel(r'$\ln d~$[kpc] (Hogg, Eilers, Rix 2018)', fontsize = fsize)
plt.savefig('paper/comparison_queiroz.pdf', pad_inches=.2, bbox_inches = 'tight')

diff = np.log(matches['BPG_meandist']) - np.log(distance_match.value/1000.)
offset = np.nanmedian(diff)
scatter = np.nanpercentile(diff, 84) - np.nanpercentile(diff, 16)
print(offset, scatter)



# -------------------------------------------------------------------------------
# HWR's suggestion: isochrones
# -------------------------------------------------------------------------------
# isochrones:
iso = Table.read('isochrones/isocz019.dat', format = 'ascii')
iso_age8 = iso['col1'] == 8.0
iso_age9 = iso['col1'] == 9.0
iso_age10 = iso['col1'] == 10.0

abs_mag_W1 = labels['w1mpro'] - 5 * np.log10(distance.value) + 5
W1_sun = 3.222
log_Lstar_Lsun = (W1_sun - abs_mag_W1)/2.5

fig, ax = plt.subplots(1, 1, figsize = (8, 7))
plt.scatter(np.log10(labels[train]['TEFF']), abs_mag_W1[train], s = 10, alpha = .5, rasterized = True, label = 'HER 2018')
#plt.ylim(-.5, -8.5)
ax.tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
plt.ylabel(r'$M_{\rm W1}$', fontsize = fsize)
plt.xlabel(r'$\log_{10}(T_{\rm eff})$', fontsize = fsize)

plt.plot(iso[iso_age8]['col5'], -2.5*iso[iso_age8]['col4'] + W1_sun, label = r'$\log(\rm age/yr) = 8$')
plt.plot(iso[iso_age9]['col5'], -2.5*iso[iso_age9]['col4'] + W1_sun, label = r'$\log(\rm age/yr) = 9$')
plt.plot(iso[iso_age10]['col5'], -2.5*iso[iso_age10]['col4'] + W1_sun, label = r'$\log(\rm age/yr) = 10$')
plt.legend(frameon = True, fontsize = fsize)
plt.ylim(8, -8)
plt.xlim(4.3, 3.5)
plt.savefig('paper/isochrones_test1.pdf', pad_inches=.2, bbox_inches = 'tight')


abs_mag_W1_schultheis = matches['w1mpro'] - 5 * np.log10(matches['Dis']*1000) + 5
abs_mag_W1_matches = matches['w1mpro'] - 5 * np.log10(distance_match.value) + 5

fig, ax = plt.subplots(1, 1, figsize = (8, 7))
plt.scatter(np.log10(matches['TEFF']), abs_mag_W1_matches, s = 10, alpha = .5, rasterized = True, label = 'HER 2018')
plt.scatter(np.log10(matches['TEFF']), abs_mag_W1_schultheis, s = 10, alpha = .5, rasterized = True, label = 'Schultheis+ 2014')
ax.tick_params(axis=u'both', direction='in', which='both', right = 'on', top = 'on')
plt.ylabel(r'$M_{\rm W1}$', fontsize = fsize)
plt.xlabel(r'$\log_{10}(T_{\rm eff})$', fontsize = fsize)

plt.plot(iso[iso_age8]['col5'], -2.5*iso[iso_age8]['col4'] + W1_sun, label = r'$\log(\rm age/yr) = 8$')
plt.plot(iso[iso_age9]['col5'], -2.5*iso[iso_age9]['col4'] + W1_sun, label = r'$\log(\rm age/yr) = 9$')
plt.plot(iso[iso_age10]['col5'], -2.5*iso[iso_age10]['col4'] + W1_sun, label = r'$\log(\rm age/yr) = 10$')
plt.legend(frameon = True, fontsize = fsize)
plt.ylim(8, -8)
plt.xlim(4.3, 3.5)
plt.savefig('paper/isochrones_test2.pdf', pad_inches=.2, bbox_inches = 'tight')







